# nodes/price_agent.py
from dotenv import load_dotenv
import requests
import os

load_dotenv(override=True)

def fetch_price_results(query: str, max_results: int = 3):
    print(f"\n{'='*60}")
    print(f"FETCH_PRICE_RESULTS CALLED")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    SERP_API_KEY = os.getenv('SERP_API_KEY')
    
    if not SERP_API_KEY:
        print("ERROR: No API key found")
        return []
    
    print(f"API Key: {SERP_API_KEY[:20]}...")
    
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": query,
        "hl": "en",
        "gl": "IN",
        "api_key": SERP_API_KEY
    }
    
    print(f"Making API request...")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Response status: {response.status_code}")
        
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        
        results = []
        if "shopping_results" in data:
            print(f"Found {len(data['shopping_results'])} shopping results")
            for item in data["shopping_results"][:max_results]:
                title = item.get("title", "No Title")
                price = item.get("price", "Not Found")
                link = item.get("link", "No URL")
                store = item.get("source", "Unknown")
                
                results.append({
                    "store": store,
                    "title": title.strip(),
                    "price": price.strip(),
                    "url": link
                })
            print(f"Returning {len(results)} results")
        else:
            print("No shopping_results key in response")
        
        return results
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def price_agent_node(state: dict) -> dict:
    print(f"\n{'#'*60}")
    print(f"PRICE_AGENT_NODE CALLED")
    print(f"{'#'*60}")
    
    product_names = state.get("products", [])
    print(f"Products: {product_names}")
    
    if not product_names:
        return {
            **state,
            "price_data": [],
            "current_step": "No products"
        }
    
    try:
        all_prices = []
        
        for product in product_names[:3]:
            print(f"\nProcessing product: {product}")
            product_prices = fetch_price_results(product)
            all_prices.append({
                "product": product,
                "prices": product_prices
            })
        
        print(f"\nFinal price_data has {len(all_prices)} items")
        for item in all_prices:
            print(f"  {item['product']}: {len(item['prices'])} prices")
        
        return {
            **state,
            "price_data": all_prices,
            "current_step": f"Price data collected for {len(all_prices)} products"
        }
    except Exception as e:
        print(f"ERROR in price_agent_node: {e}")
        return {
            **state,
            "price_data": [],
            "current_step": f"Failed: {str(e)}"
        }