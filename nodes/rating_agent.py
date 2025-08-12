# nodes/rating_agent.py - FIXED
import requests
import os

def fetch_platform_ratings(product_name: str, max_results: int = 3):
    """Fetches rating and review count from Google Shopping results."""
    SERP_API_KEY = os.getenv('SERP_API_KEY')
    
    if not SERP_API_KEY:
        return []
    
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": product_name,
        "hl": "en",
        "gl": "IN",
        "api_key": SERP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        ratings_info = []
        
        if "shopping_results" in data:
            for item in data["shopping_results"][:max_results]:
                title = item.get("title", "No Title")
                link = item.get("link", "")
                source = item.get("source", "Unknown Store")
                rating = item.get("rating", "N/A")
                reviews_count = item.get("reviews", "N/A")
                
                ratings_info.append({
                    "platform": source,
                    "title": title,
                    "rating": rating,
                    "total_reviews": reviews_count,
                    "platform_url": link
                })
        
        return ratings_info
    except Exception as e:
        return []

def rating_platform_agent_node(state: dict) -> dict:
    """
    LangGraph-style node that fetches rating and review count from multiple platforms.
    """
    product_names = state.get("products", [])
    
    try:
        platform_ratings = []
        
        for product in product_names[:3]:  # Limit to 3 products
            ratings = fetch_platform_ratings(product)
            platform_ratings.append({
                "product": product,
                "ratings": ratings
            })
        
        return {
            **state,
            "platform_rating_data": platform_ratings,
            "current_step": f"Rating data collected for {len(platform_ratings)} products"
        }
    except Exception as e:
        return {
            **state,
            "platform_rating_data": [],
            "current_step": f"Rating collection failed: {str(e)}"
        }