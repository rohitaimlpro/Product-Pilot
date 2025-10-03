# nodes/product_info_agent.py - FIXED
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()

def fetch_product_info_snippets(query: str, max_results: int = 3):
    """Fetch product overview/info snippets from Google using SerpAPI."""
    SERP_API_KEY = os.getenv('SERP_API_KEY')
    
    if not SERP_API_KEY:
        print(f"❌ SERP_API_KEY not found in product_info_agent for: {query}")
        return []
    
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query + " specifications features",
        "hl": "en",
        "gl": "IN",
        "api_key": SERP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        snippets = []
        if "organic_results" in data:
            for result in data["organic_results"][:max_results]:
                snippet = result.get("snippet", "")
                title = result.get("title", "")
                link = result.get("link", "")
                
                if snippet:
                    snippets.append({
                        "title": title.strip(),
                        "snippet": snippet.strip(),
                        "link": link
                    })
        
        print(f"✅ Found {len(snippets)} info snippets for {query}")
        return snippets
    except Exception as e:
        print(f"❌ Error fetching product info for {query}: {str(e)}")
        return []

def product_info_agent_node(state: dict) -> dict:
    """
    LangGraph-style node that takes a list of product names and fetches
    general product information (overview/details) using web search.
    """
    product_names = state.get("products", [])
    
    if not product_names:
        print("⚠️ No products to fetch info for")
        return {
            **state,
            "product_info": [],
            "current_step": "No products for info collection"
        }
    
    try:
        all_info = []
        
        for product in product_names[:3]:
            print(f"🔍 Fetching product info for: {product}")
            product_snippets = fetch_product_info_snippets(product)
            all_info.append({
                "product": product,
                "info": product_snippets
            })
        
        print(f"✅ Product info collected for {len(all_info)} products")
        return {
            **state,
            "product_info": all_info,
            "current_step": f"Product info collected for {len(all_info)} products"
        }
    except Exception as e:
        print(f"❌ Product info collection failed: {str(e)}")
        return {
            **state,
            "product_info": [],
            "current_step": f"Product info collection failed: {str(e)}"
        }