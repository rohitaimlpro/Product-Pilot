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
