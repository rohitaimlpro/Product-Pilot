# nodes/review_agent.py - FIXED
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
import os

def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

def fetch_review_snippets(query):
    """Fetch review snippets for a product from Google Search via SerpAPI."""
    SERP_API_KEY = os.getenv('SERP_API_KEY')
    
    if not SERP_API_KEY:
        return []
    
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query + " user reviews",
        "hl": "en",
        "gl": "IN",
        "api_key": SERP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        snippets = []
        if "organic_results" in data:
            for result in data["organic_results"][:5]:  # Limit to 5 results
                snippet = result.get("snippet", "")
                if snippet:
                    snippets.append(snippet)
        
        return snippets
    except Exception as e:
        return []

def classify_reviews_with_llm(snippets, llm):
    """Classify reviews as positive or negative using an LLM."""
    
    if not snippets:
        return {"positive_reviews": [], "negative_reviews": []}
    
    try:
        # Combine snippets for batch processing
        combined_snippets = "\n---\n".join(snippets[:5])  # Limit snippets
        
        prompt = f"""
        Analyze these review snippets and categorize them as positive or negative:
        
        {combined_snippets}
        
        Return your analysis in this format:
        POSITIVE:
        - [positive points]
        
        NEGATIVE:
        - [negative points]
        """
        
        result = llm.invoke(prompt)
        response_text = result.content if hasattr(result, 'content') else str(result)
        
        # Simple parsing of the response
        positive_reviews = []
        negative_reviews = []
        
        if "POSITIVE:" in response_text:
            pos_section = response_text.split("POSITIVE:")[1].split("NEGATIVE:")[0]
            positive_reviews = [line.strip("- ").strip() for line in pos_section.split("\n") if line.strip().startswith("-")]
        
        if "NEGATIVE:" in response_text:
            neg_section = response_text.split("NEGATIVE:")[1]
            negative_reviews = [line.strip("- ").strip() for line in neg_section.split("\n") if line.strip().startswith("-")]
        
        return {
            "positive_reviews": positive_reviews[:3],
            "negative_reviews": negative_reviews[:3]
        }
    except Exception:
        return {"positive_reviews": [], "negative_reviews": []}

def review_rating_agent_node(state: dict) -> dict:
    """
    LangGraph-style node that processes a list of products and fetches review info
    """
    product_names = state.get("products", [])
    
    try:
        llm = get_llm()
        review_data = []
        
        for product in product_names[:3]:  # Limit to 3 products
            snippets = fetch_review_snippets(product)
            classified_reviews = classify_reviews_with_llm(snippets, llm)
            
            review_data.append({
                "product": product,
                "reviews": classified_reviews
            })
        
        return {
            **state,
            "review_data": review_data,
            "current_step": f"Review data collected for {len(review_data)} products"
        }
    except Exception as e:
        return {
            **state,
            "review_data": [],
            "current_step": f"Review collection failed: {str(e)}"
        }