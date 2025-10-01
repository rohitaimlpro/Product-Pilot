import os
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any

def intent_classifier_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced intent classifier that properly distinguishes between comparison and recommendation queries
    """
    
    user_input = state.get("input", "")
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Enhanced prompt with clear examples
    prompt = f"""You are an intent classification system for a product recommendation assistant.

Your task: Classify the user's query into ONE of these intents:
1. "comparison" - User wants to compare 2 or more specific products
2. "recommendation" - User wants suggestions for products based on requirements

CRITICAL RULES:
- If the query mentions "compare", "versus", "vs", "vs.", "difference between" = ALWAYS return "comparison"
- If the query contains 2+ specific product names/models = ALWAYS return "comparison"
- If the query asks for suggestions, recommendations, or describes needs = return "recommendation"

Examples:
- "compare iphone 14 vs iphone 15" → "comparison"
- "iPhone 14 versus Samsung Galaxy S23" → "comparison"
- "what's the difference between MacBook Air and MacBook Pro" → "comparison"
- "compare Dell XPS 13 and HP Spectre x360" → "comparison"
- "I need a good laptop for gaming" → "recommendation"
- "recommend a smartphone under $500" → "recommendation"
- "best wireless earbuds" → "recommendation"

User Query: "{user_input}"

Respond with ONLY one word: either "comparison" or "recommendation"
No explanation, no additional text, just the intent."""

    try:
        response = llm.invoke(prompt)
        intent = response.content.strip().lower()
        
        # Validate and clean response
        if "comparison" in intent:
            intent = "comparison"
        elif "recommendation" in intent:
            intent = "recommendation"
        else:
            # Fallback: check for comparison keywords in original query
            comparison_keywords = ["compare", "versus", "vs", "vs.", "difference between", "better than"]
            if any(keyword in user_input.lower() for keyword in comparison_keywords):
                intent = "comparison"
            else:
                intent = "recommendation"
        
        print(f"✅ Intent classified as: {intent}")
        
        # Update state
        state["intent"] = intent
        state["current_step"] = f"Intent classified: {intent}"
        
    except Exception as e:
        print(f"❌ Error in intent classification: {str(e)}")
        # Default to recommendation on error
        state["intent"] = "recommendation"
        state["current_step"] = f"Intent classification error (defaulted to recommendation): {str(e)}"
    
    return state