import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

_llm = None

def get_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=1,
            model_kwargs={
                "generation_config": {
                    "thinking_config": {"thinking_budget": 512}
                }
            }
        )
    return _llm


def reflection_node(state: dict) -> dict:
    """
    Pre-analysis self-check between supervisor and analyzer.
    Identifies what is well-supported vs uncertain so the analyzer
    can produce a grounded, honest response.
    """
    confidence = state.get("confidence_score", 0)

    data_summary = {
        "product_info": "available" if state.get("product_info") else "missing",
        "price_data": "available" if state.get("price_data") else "missing",
        "review_data": "available" if state.get("review_data") else "missing",
        "platform_ratings": "available" if state.get("platform_rating_data") else "missing",
    }

    prompt = f"""You are reviewing data collected to answer this user query:
"{state.get("input")}"

Products analyzed: {state.get("products")}
Overall confidence score: {confidence}/10
Agents executed: {state.get("agents_executed", [])}

Data availability:
- Product specifications: {data_summary["product_info"]}
- Pricing: {data_summary["price_data"]}
- User reviews: {data_summary["review_data"]}
- Platform ratings: {data_summary["platform_ratings"]}

In 2-3 concise sentences:
1. What aspects of the recommendation are well-supported by collected data?
2. What is uncertain or missing that the final answer should explicitly acknowledge?"""

    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        analysis_context = response.content.strip()
    except Exception as e:
        logger.error("Reflection failed: %s", e)
        analysis_context = f"Reflection unavailable: {e}"

    logger.info("Reflection complete: %s", analysis_context[:100])

    return {
        **state,
        "analysis_context": analysis_context,
        "current_step": "Pre-analysis reflection complete",
    }
