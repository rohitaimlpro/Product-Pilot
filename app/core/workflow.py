from langgraph.graph import StateGraph, END
from app.models.graph_state import GraphState
from nodes.supervisor_agent import supervisor_agent_node
from nodes.reflection_node import reflection_node
from nodes.analyzer_agent import analyzer_agent_node


def create_workflow():
    workflow = StateGraph(GraphState)

    workflow.add_node("supervisor", supervisor_agent_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("analyzer", analyzer_agent_node)

    workflow.set_entry_point("supervisor")
    workflow.add_edge("supervisor", "reflection")
    workflow.add_edge("reflection", "analyzer")
    workflow.add_edge("analyzer", END)

    return workflow.compile()
