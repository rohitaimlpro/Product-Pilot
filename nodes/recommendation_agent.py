import os
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any
import json
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv(override=True)

# Rest of the code...

def recommendation_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced recommendation agent that generates product suggestions based on user requirements
    and ALWAYS returns at least 2-3 products
    """
    
    user_input = state.get("input", "")
    
    # Try to get products from SERP API first
    try:
        serpapi_key = os.getenv("SERP_API_KEY")
        if serpapi_key:
            search_query = f"{user_input} best products to buy"
            url = "https://serpapi.com/search"
            params = {
                "q": search_query,
                "api_key": serpapi_key,
                "engine": "google"
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                products = []
                
                # Extract product names from shopping results
                if "shopping_results" in data:
                    for item in data["shopping_results"][:3]:
                        products.append(item.get("title", ""))
                
                # If not enough products, try organic results
                if len(products) < 2 and "organic_results" in data:
                    for item in data["organic_results"][:5]:
                        title = item.get("title", "")
                        if title and title not in products:
                            products.append(title)
                            if len(products) >= 3:
                                break
                
                # Clean and filter products
                products = [p.strip() for p in products if p.strip()][:3]
                
                if len(products) >= 2:
                    print(f"✅ SERP API found {len(products)} products: {products}")
                    state["products"] = products
                    state["current_step"] = f"Recommendations generated: {len(products)} products"
                    return state
    except Exception as e:
        print(f"⚠️ SERP API error: {str(e)}")
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,  # Slightly higher for creative product suggestions
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    prompt = f"""You are a product recommendation expert. Based on the user's query, suggest 2-3 specific product names/models.

CRITICAL RULES:
1. Return REAL, SPECIFIC product names (not generic categories)
2. Include brand names and model numbers where applicable
3. Return AT LEAST 2 products, ideally 3
4. Format as a JSON array of strings
5. Be realistic about current products available in the market

User Query: "{user_input}"

Examples of GOOD responses:
- ["iPhone 15 Pro", "Samsung Galaxy S24 Ultra", "Google Pixel 8 Pro"]
- ["Dell XPS 13", "MacBook Air M2", "HP Spectre x360"]
- ["Sony WH-1000XM5", "Bose QuietComfort 45", "Apple AirPods Max"]

Examples of BAD responses:
- ["smartphone", "phone"]  ❌ Too generic
- ["iPhone"]  ❌ Not specific enough, needs model
- ["laptop"]  ❌ Not a real product

Now generate 2-3 specific product recommendations for the query above.
Respond with ONLY a JSON array of product names, nothing else.
Format: ["Product 1", "Product 2", "Product 3"]"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Try to parse as JSON
        try:
            products = json.loads(content)
            if isinstance(products, list) and len(products) > 0:
                # Clean product names
                products = [str(p).strip() for p in products if p]
                print(f"✅ Recommendation agent generated {len(products)} products: {products}")
            else:
                raise ValueError("Empty or invalid product list")
        except:
            # Fallback parsing: extract from text
            print(f"⚠️ JSON parsing failed, attempting text extraction from: {content}")
            
            # Try to extract product names from response
            import re
            # Look for quoted strings or list items
            quoted_items = re.findall(r'["\']([^"\']+)["\']', content)
            if quoted_items:
                products = quoted_items[:3]  # Take up to 3 items
            else:
                # Split by common delimiters
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                products = [re.sub(r'^[-*•]\s*', '', line) for line in lines if line][:3]
            
            if not products:
                # Ultimate fallback based on query keywords
                print("⚠️ No products extracted, using intelligent fallback")
                products = generate_fallback_products(user_input)
        
        # Ensure we have at least 2 products
        if len(products) < 2:
            print(f"⚠️ Only {len(products)} product(s) found, adding fallbacks")
            products.extend(generate_fallback_products(user_input, exclude=products))
            products = products[:3]  # Limit to 3
        
        # Update state
        state["products"] = products
        state["current_step"] = f"Recommendations generated: {len(products)} products"
        
        print(f"✅ Final products: {products}")
        
    except Exception as e:
        print(f"❌ Error in recommendation agent: {str(e)}")
        # Generate fallback products based on query
        state["products"] = generate_fallback_products(user_input)
        state["current_step"] = f"Recommendation error (using fallbacks): {str(e)}"
    
    return state


def generate_fallback_products(query: str, exclude: list = None) -> list:
    """
    Generate intelligent fallback products based on query keywords
    """
    if exclude is None:
        exclude = []
    
    query_lower = query.lower()
    products = []
    
    # Smartphone fallbacks
    if any(word in query_lower for word in ["phone", "smartphone", "iphone", "android"]):
        candidates = ["iPhone 15 Pro", "Samsung Galaxy S24", "Google Pixel 8 Pro"]
        products = [p for p in candidates if p not in exclude][:3]
    
    # Laptop fallbacks
    elif any(word in query_lower for word in ["laptop", "notebook", "macbook", "computer"]):
        candidates = ["MacBook Air M2", "Dell XPS 13", "HP Spectre x360"]
        products = [p for p in candidates if p not in exclude][:3]
    
    # Headphones/earbuds fallbacks
    elif any(word in query_lower for word in ["headphone", "earbud", "airpod", "audio"]):
        candidates = ["Sony WH-1000XM5", "Apple AirPods Pro", "Bose QuietComfort 45"]
        products = [p for p in candidates if p not in exclude][:3]
    
    # Tablet fallbacks
    elif any(word in query_lower for word in ["tablet", "ipad"]):
        candidates = ["iPad Air", "Samsung Galaxy Tab S9", "Microsoft Surface Pro 9"]
        products = [p for p in candidates if p not in exclude][:3]
    
    # Smartwatch fallbacks
    elif any(word in query_lower for word in ["watch", "smartwatch", "wearable"]):
        candidates = ["Apple Watch Series 9", "Samsung Galaxy Watch 6", "Garmin Fenix 7"]
        products = [p for p in candidates if p not in exclude][:3]
    
    # Camera fallbacks
    elif any(word in query_lower for word in ["camera", "dslr", "mirrorless"]):
        candidates = ["Sony A7 IV", "Canon EOS R6", "Nikon Z6 II"]
        products = [p for p in candidates if p not in exclude][:3]
    
    # Generic tech fallbacks
    else:
        candidates = ["iPhone 15 Pro", "Samsung Galaxy S24", "MacBook Air M2"]
        products = [p for p in candidates if p not in exclude][:3]
    
    # Ensure we return at least 2 products
    if len(products) < 2:
        fallback_pool = ["iPhone 15 Pro", "Samsung Galaxy S24", "MacBook Air M2", 
                        "Dell XPS 13", "Sony WH-1000XM5", "iPad Air"]
        for item in fallback_pool:
            if item not in exclude and item not in products:
                products.append(item)
                if len(products) >= 3:
                    break
    
    return products[:3]