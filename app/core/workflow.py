from langgraph.graph import StateGraph, END
from app.models.graph_state import GraphState
from nodes.intent_classifier import intent_classifier_node
from nodes.product_extractor import extract_product_names_node
from nodes.recommendation_agent import recommendation_agent_node
from nodes.supervisor_agent import supervisor_agent_node
from nodes.reflection_node import reflection_node
from nodes.analyzer_agent import analyzer_agent_node


def create_workflow():
    workflow = StateGraph(GraphState)

    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("extract_products", extract_product_names_node)
    workflow.add_node("recommendation_agent", recommendation_agent_node)
    workflow.add_node("supervisor", supervisor_agent_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("analyzer", analyzer_agent_node)
    workflow.set_entry_point("intent_classifier")

    def route_intent(state: GraphState) -> str:
        intent = state.get("intent", "")
        if "comparison" in intent.lower():
            return "extract_products"
        return "recommendation_agent"

    workflow.add_conditional_edges(
        "intent_classifier", route_intent,
        {
            "recommendation_agent": "recommendation_agent",
            "extract_products": "extract_products",
        }
    )

    # Supervisor now runs all agents in parallel internally — no graph loop needed
    workflow.add_edge("recommendation_agent", "supervisor")
    workflow.add_edge("extract_products", "supervisor")
    workflow.add_edge("supervisor", "reflection")
    workflow.add_edge("reflection", "analyzer")
    workflow.add_edge("analyzer", END)

    return workflow.compile()
