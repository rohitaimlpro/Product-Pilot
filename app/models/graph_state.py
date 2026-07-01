from typing import TypedDict, List, Dict

class GraphState(TypedDict):
    input: str
    intent: str
    products: List[str]
    price_data: List[Dict]
    review_data: List[Dict]
    product_info: List[Dict]
    platform_rating_data: List[Dict]
    final_recommendation: str
    current_step: str
    missing_data: List[str]
    collection_complete: bool
    search_hints: Dict[str, str]       # product → reformulated query on retry
    confidence_score: int              # supervisor's 1-10 confidence before analysis
    analysis_context: str              # reflection node output fed to analyzer
    agent_plan: List[str]             # query-aware ordered list of agents to run
    agents_executed: List[str]        # tracks which agents have completed
