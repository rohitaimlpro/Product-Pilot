
# from langchain_google_genai import ChatGoogleGenerativeAI
# import os

# def get_llm():
#     return ChatGoogleGenerativeAI(
#         model="gemini-2.5-flash",
#         temperature=0.3,
#         google_api_key=os.getenv("GOOGLE_API_KEY")
#     )

# def analyzer_agent_node(state: dict) -> dict:
#     """
#     Combines output from all agents and creates a comprehensive product analysis
#     """
#     try:
#         llm = get_llm()
        
#         products = state.get("products", [])
#         price_data = state.get("price_data", [])
#         review_data = state.get("review_data", [])
#         product_info = state.get("product_info", [])
#         platform_rating_data = state.get("platform_rating_data", [])
#         user_input = state.get("input", "")
        
#         if not products:
#             return {
#                 **state,
#                 "final_recommendation": "I couldn't identify specific products from your query. Please try being more specific about what you're looking for.",
#                 "current_step": "Analysis complete - no products found"
#             }
        
#         # Create a comprehensive prompt with all available data
#         data_summary = f"""
#         User Query: {user_input}
#         Products to analyze: {products}
        
#         Available Data:
#         - Price Data: {len(price_data)} entries
#         - Review Data: {len(review_data)} entries  
#         - Product Info: {len(product_info)} entries
#         - Rating Data: {len(platform_rating_data)} entries
        
#         Detailed Data:
#         Price Information: {price_data}
#         Reviews: {review_data}
#         Product Details: {product_info}
#         Ratings: {platform_rating_data}
#         """
        
#         prompt = f"""
#         You are a knowledgeable product advisor. Based on the following information, provide a comprehensive recommendation:

#         {data_summary}

#         Please provide:
#         1. A clear recommendation addressing the user's query
#         2. Key features and benefits of recommended products
#         3. Price ranges if available
#         4. Any important considerations
#         5. Final verdict/recommendation

#         Make your response helpful, informative, and well-structured. If data is limited, use your knowledge to provide valuable insights.
#         """
        
#         response = llm.invoke(prompt)
#         final_recommendation = response.content if hasattr(response, "content") else str(response)
        
#         return {
#             **state,
#             "final_recommendation": final_recommendation,
#             "current_step": "Analysis complete"
#         }
        
#     except Exception as e:
#         return {
#             **state,
#             "final_recommendation": f"I encountered an error while analyzing the products: {str(e)}. Please try again or check your API configuration.",
#             "current_step": f"Analysis failed: {str(e)}"
#         }
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import json

logger = logging.getLogger(__name__)


def get_llm():
    # thinking_budget=256 caps reasoning for faster responses
    # while still producing well-reasoned comparisons
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=1,  # required when using thinking_budget
        google_api_key=os.getenv("GOOGLE_API_KEY"),
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

========================
🚨 STRICT RULES (MANDATORY)
========================
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
        response = llm.invoke(prompt)

        final_recommendation = (
            response.content
            if hasattr(response, "content")
            else str(response)
        )

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