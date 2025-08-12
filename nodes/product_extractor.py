# nodes/product_extractor.py - FIXED
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import re

def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.1,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

def extract_product_names(user_input: str) -> List[str]:
    """Uses LLM to extract product names from the input."""
    try:
        llm = get_llm()
        
        prompt = f"""
        Extract specific product names from this query: "{user_input}"
        
        Return only the product names separated by commas, nothing else.
        For example: "iPhone 15, Samsung Galaxy S24"
        
        If no specific products are mentioned, return an empty response.
        """
        
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        if content and content.lower() not in ['none', 'empty', '']:
            # Split by comma and clean up
            products = [name.strip() for name in content.split(',') if name.strip()]
            return products
        
        return []
    except Exception as e:
        return []

def extract_product_names_node(state: dict) -> dict:
    """
    LangGraph node that extracts product names from user input
    """
    user_input = state.get("input", "")
    
    try:
        product_names = extract_product_names(user_input)
        
        return {
            **state,
            "products": product_names,
            "current_step": f"Products extracted: {product_names}"
        }
    except Exception as e:
        return {
            **state,
            "products": [],
            "current_step": f"Product extraction failed: {str(e)}"
        }
