import json
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.llm_utils import invoke_with_retry
from app.core.config import GEMINI_MODEL, GOOGLE_API_KEY

logger = logging.getLogger(__name__)


def get_llm():
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=1,
        google_api_key=GOOGLE_API_KEY,
        model_kwargs={
            "generation_config": {
                "thinking_config": {"thinking_budget": 256}
            }
        }
    )


def analyzer_agent_node(state: dict) -> dict:
    """
    Combines output from all agents and creates a STRICTLY GROUNDED product analysis.
    The LLM MUST rely only on retrieved SerpAPI data.
    """

    try:
        llm = get_llm()

        # -----------------------------
        # Extract state safely
        # -----------------------------
        products = state.get("products", [])
        price_data = state.get("price_data", [])
        review_data = state.get("review_data", [])
        product_info = state.get("product_info", [])
        platform_rating_data = state.get("platform_rating_data", [])
        user_input = state.get("input", "")

        if not products:
            return {
                **state,
                "final_recommendation":
                    "I couldn't identify specific products from your query. "
                    "Please mention product names clearly.",
                "current_step": "Analysis complete - no products found"
            }

        # -----------------------------
        # Convert data into clean JSON context
        # (VERY IMPORTANT FOR GROUNDING)
        # -----------------------------
        structured_context = {
            "user_query": user_input,
            "products": products,
            "price_data": price_data,
            "review_data": review_data,
            "product_info": product_info,
            "platform_ratings": platform_rating_data
        }

        context_text = json.dumps(structured_context, indent=2, ensure_ascii=False)

        # -----------------------------
        # STRICT ANTI-HALLUCINATION PROMPT
        # -----------------------------
        prompt = f"""
You are an AI Product Analysis Engine.

STRICT RULES:
─────────────
1. Use ONLY the PRODUCT DATA provided below.
2. DO NOT use your internal knowledge.
3. DO NOT assume release dates or missing facts.
4. DO NOT say "I don't have information" if data exists.
5. If data is missing, explicitly say:
   "Not available in retrieved data."
6. Treat retrieved data as the SINGLE SOURCE OF TRUTH.

========================
PRODUCT DATA (FROM SERPAPI)
========================
{context_text}

========================
TASK
========================
Analyze the products and answer the user's query.

Provide:

1. Direct recommendation answering the query
2. Feature comparison based ONLY on data
3. Price insights (if available)
4. Review & rating insights (if available)
5. Important buying considerations
6. Final verdict

========================
OUTPUT STYLE
========================
- Clear headings
- Professional advisor tone
- No speculation
- No external knowledge
- Ground every claim in provided data
"""

        logger.debug("Context sent to LLM (first 1500 chars): %s", context_text[:1500])

        # -----------------------------
        # LLM Call
        # -----------------------------
        final_recommendation = invoke_with_retry(llm, prompt, context="analyzer")

        return {
            **state,
            "final_recommendation": final_recommendation,
            "current_step": "Analysis complete"
        }

    except Exception as e:
        return {
            **state,
            "final_recommendation":
                f"I encountered an error while analyzing products: {str(e)}",
            "current_step": f"Analysis failed: {str(e)}"
        }