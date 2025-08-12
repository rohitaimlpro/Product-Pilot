# nodes/price_agent.py - FIXED
import requests
import os

def fetch_price_results(query: str, max_results: int = 3):
    SERP_API_KEY = os.getenv('SERP_API_KEY')
    
    if not SERP_API_KEY:
        return []
    
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": query,
        "hl": "en",
        "gl": "IN",
        "api_key": SERP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        results = []
        if "shopping_results" in data:
            for item in data["shopping_results"][:max_results]:
                title = item.get("title", "No Title Found")
                price = item.get("price", "Not Found")
                link = item.get("link", "No URL Found")
                store = item.get("source", "Unknown Store")
                
                results.append({
                    "store": store,
                    "title": title.strip(),
                    "price": price.strip(),
                    "url": link
                })
        
        return results
    except Exception as e:
        return []

def price_agent_node(state: dict) -> dict:
    """
    LangGraph-style node that processes a list of products and fetches price info
    """
    product_names = state.get("products", [])
    
    try:
        all_prices = []
        
        for product in product_names[:3]:  # Limit to 3 products
            product_prices = fetch_price_results(product)
            all_prices.append({
                "product": product,
                "prices": product_prices
            })
        
        return {
            **state,
            "price_data": all_prices,
            "current_step": f"Price data collected for {len(all_prices)} products"
        }
    except Exception as e:
        return {
            **state,
            "price_data": [],
            "current_step": f"Price collection failed: {str(e)}"
        }
