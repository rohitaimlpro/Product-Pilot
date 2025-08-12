# nodes/analyzer_agent.py - FIXED
from langchain_google_genai import ChatGoogleGenerativeAI
import os

def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.3,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

def analyzer_agent_node(state: dict) -> dict:
    """
    Combines output from all agents and creates a comprehensive product analysis
    """
    try:
        llm = get_llm()
        
        products = state.get("products", [])
        price_data = state.get("price_data", [])
        review_data = state.get("review_data", [])
        product_info = state.get("product_info", [])
        platform_rating_data = state.get("platform_rating_data", [])
        user_input = state.get("input", "")
        
        if not products:
            return {
                **state,
                "final_recommendation": "I couldn't identify specific products from your query. Please try being more specific about what you're looking for.",
                "current_step": "Analysis complete - no products found"
            }
        
        # Create a comprehensive prompt with all available data
        data_summary = f"""
        User Query: {user_input}
        Products to analyze: {products}
        
        Available Data:
        - Price Data: {len(price_data)} entries
        - Review Data: {len(review_data)} entries  
        - Product Info: {len(product_info)} entries
        - Rating Data: {len(platform_rating_data)} entries
        
        Detailed Data:
        Price Information: {price_data}
        Reviews: {review_data}
        Product Details: {product_info}
        Ratings: {platform_rating_data}
        """
        
        prompt = f"""
        You are a knowledgeable product advisor. Based on the following information, provide a comprehensive recommendation:

        {data_summary}

        Please provide:
        1. A clear recommendation addressing the user's query
        2. Key features and benefits of recommended products
        3. Price ranges if available
        4. Any important considerations
        5. Final verdict/recommendation

        Make your response helpful, informative, and well-structured. If data is limited, use your knowledge to provide valuable insights.
        """
        
        response = llm.invoke(prompt)
        final_recommendation = response.content if hasattr(response, "content") else str(response)
        
        return {
            **state,
            "final_recommendation": final_recommendation,
            "current_step": "Analysis complete"
        }
        
    except Exception as e:
        return {
            **state,
            "final_recommendation": f"I encountered an error while analyzing the products: {str(e)}. Please try again or check your API configuration.",
            "current_step": f"Analysis failed: {str(e)}"
        }
