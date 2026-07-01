from langgraph.graph import StateGraph, END
from app.models.graph_state import GraphState
from nodes.query_parser import query_parser_node
from nodes.recommendation_agent import recommendation_agent_node
from nodes.supervisor_agent import supervisor_agent_node
from nodes.reflection_node import reflection_node
from nodes.analyzer_agent import analyzer_agent_node


def create_workflow():
    workflow = StateGraph(GraphState)

    workflow.add_node("query_parser", query_parser_node)
    workflow.add_node("recommendation_agent", recommendation_agent_node)
    workflow.add_node("supervisor", supervisor_agent_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("analyzer", analyzer_agent_node)
    workflow.set_entry_point("query_parser")

    def route_intent(state: GraphState) -> str:
        intent = state.get("intent", "")
        if "comparison" in intent.lower():
            return "supervisor"
        return "recommendation_agent"

    workflow.add_conditional_edges(
        "query_parser", route_intent,
        {
            "supervisor": "supervisor",
            "recommendation_agent": "recommendation_agent",
        }
    )

    workflow.add_edge("recommendation_agent", "supervisor")
    workflow.add_edge("supervisor", "reflection")
    workflow.add_edge("reflection", "analyzer")
    workflow.add_edge("analyzer", END)

    return workflow.compile()
