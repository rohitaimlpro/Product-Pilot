from langgraph.graph import StateGraph, END
from app.models.graph_state import GraphState
from nodes.supervisor_agent import supervisor_agent_node
from nodes.reflect_and_score import reflect_and_score_node
from nodes.analyzer_agent import analyzer_agent_node


def create_workflow():
    workflow = StateGraph(GraphState)

    workflow.add_node("supervisor", supervisor_agent_node)
    workflow.add_node("reflect_and_score", reflect_and_score_node)
    workflow.add_node("analyzer", analyzer_agent_node)

    workflow.set_entry_point("supervisor")
    workflow.add_edge("supervisor", "reflect_and_score")
    workflow.add_edge("reflect_and_score", "analyzer")
    workflow.add_edge("analyzer", END)

    return workflow.compile()
