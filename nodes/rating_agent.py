# nodes/rating_agent.py - FIXED
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv(override=True)

def fetch_platform_ratings(product_name: str, max_results: int = 3):
    """Fetches rating and review count from Google Shopping results."""
    SERP_API_KEY = os.getenv('SERP_API_KEY')
    
    if not SERP_API_KEY:
        print(f"❌ SERP_API_KEY not found in rating_agent for: {product_name}")
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
        response.raise_for_status()
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
        
        print(f"✅ Found {len(ratings_info)} ratings for {product_name}")
        return ratings_info
    except Exception as e:
        print(f"❌ Error fetching ratings for {product_name}: {str(e)}")
        return []

def rating_platform_agent_node(state: dict) -> dict:
    """
    LangGraph-style node that fetches rating and review count from multiple platforms.
    """
    product_names = state.get("products", [])
    
    if not product_names:
        print("⚠️ No products to fetch ratings for")
        return {
            **state,
            "platform_rating_data": [],
            "current_step": "No products for rating collection"
        }
    
    try:
        platform_ratings = []
        
        for product in product_names[:3]:
            print(f"🔍 Fetching ratings for: {product}")
            ratings = fetch_platform_ratings(product)
            platform_ratings.append({
                "product": product,
                "ratings": ratings
            })
        
        print(f"✅ Rating data collected for {len(platform_ratings)} products")
        return {
            **state,
            "platform_rating_data": platform_ratings,
            "current_step": f"Rating data collected for {len(platform_ratings)} products"
        }
    except Exception as e:
        print(f"❌ Rating collection failed: {str(e)}")
        return {
            **state,
            "platform_rating_data": [],
            "current_step": f"Rating collection failed: {str(e)}"
        }