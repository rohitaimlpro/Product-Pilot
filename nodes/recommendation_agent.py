# nodes/recommendation_agent.py - FIXED
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import re

def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.3,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

def recommendation_agent_node(state: dict) -> dict:
    """
    Generates product recommendations based on user input
    """
    user_input = state.get("input", "")
    
    try:
        llm = get_llm()
        
        prompt = f"""
        Based on this user query: "{user_input}"
        
        Generate 2-3 specific, popular product recommendations that match the requirements.
        
        Return only the product names separated by commas, nothing else.
        For example: "MacBook Air M2, Dell XPS 13, ThinkPad X1 Carbon"
        
        Focus on well-known, popular products.
        """
        
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        if content:
            # Split by comma and clean up
            products = [name.strip() for name in content.split(',') if name.strip()]
        else:
            products = []
        
        return {
            **state,
            "products": products,
            "current_step": f"Recommendations generated: {products}"
        }
    except Exception as e:
        return {
            **state,
            "products": [],
            "current_step": f"Recommendation generation failed: {str(e)}"
        }