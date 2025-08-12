# nodes/intent_classifier.py - FIXED
from langchain_google_genai import ChatGoogleGenerativeAI
import os

def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.1,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

def intent_classifier_node(state: dict) -> dict:
    """
    Classifies user intent as either 'recommendation' or 'comparison'
    """
    user_input = state.get("input", "")
    
    try:
        llm = get_llm()
        
        prompt = f"""
        Analyze the following user query and classify the intent as either "recommendation" or "comparison":
        
        Query: "{user_input}"
        
        - If the user is asking for product suggestions/recommendations, respond with "recommendation"
        - If the user wants to compare specific products, respond with "comparison"
        
        Respond with only one word: "recommendation" or "comparison"
        """
        
        response = llm.invoke(prompt)
        intent = response.content.strip().lower()
        
        return {
            **state,
            "intent": intent,
            "current_step": "Intent classified"
        }
    except Exception as e:
        return {
            **state,
            "intent": "recommendation",  # default fallback
            "current_step": f"Intent classification failed: {str(e)}"
        }
