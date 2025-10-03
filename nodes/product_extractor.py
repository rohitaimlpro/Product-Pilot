import os
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any
import json
import re
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Rest of the code...

def extract_product_names_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced product extractor that reliably extracts product names from comparison queries
    """
    
    user_input = state.get("input", "")
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    prompt = f"""You are a product name extraction expert. Extract ALL product names from the user's query.

CRITICAL RULES:
1. Extract EVERY product mentioned (including brand + model)
2. Keep full product names intact (e.g., "iPhone 14 Pro Max" not just "iPhone")
3. Include model numbers and versions
4. Return as a JSON array of strings
5. Each product should be a complete, specific name

User Query: "{user_input}"

Examples:
Query: "compare iphone 14 vs iphone 15"
Response: ["iPhone 14", "iPhone 15"]

Query: "iPhone 14 Pro versus Samsung Galaxy S23 Ultra"
Response: ["iPhone 14 Pro", "Samsung Galaxy S23 Ultra"]

Query: "MacBook Air M2 vs Dell XPS 13 vs HP Spectre x360"
Response: ["MacBook Air M2", "Dell XPS 13", "HP Spectre x360"]

Query: "difference between PS5 and Xbox Series X"
Response: ["PlayStation 5", "Xbox Series X"]

Now extract product names from the query above.
Respond with ONLY a JSON array of product names, nothing else.
Format: ["Product 1", "Product 2"]"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Try to parse as JSON
        try:
            products = json.loads(content)
            if isinstance(products, list) and len(products) > 0:
                products = [str(p).strip() for p in products if p]
                print(f"✅ Extracted {len(products)} products: {products}")
            else:
                raise ValueError("Empty or invalid product list")
        except:
            # Fallback parsing
            print(f"⚠️ JSON parsing failed, attempting text extraction from: {content}")
            products = fallback_product_extraction(user_input, content)
        
        # If still no products, use regex-based extraction
        if not products or len(products) == 0:
            print("⚠️ LLM extraction failed, using regex fallback")
            products = regex_product_extraction(user_input)
        
        # Ensure we have at least 2 products for comparison
        if len(products) < 2:
            print(f"⚠️ Only {len(products)} product(s) found, attempting enhanced extraction")
            products = enhanced_extraction(user_input)
        
        # Update state
        state["products"] = products
        state["current_step"] = f"Products extracted: {len(products)} items"
        
        print(f"✅ Final extracted products: {products}")
        
    except Exception as e:
        print(f"❌ Error in product extraction: {str(e)}")
        # Last resort: regex extraction
        state["products"] = regex_product_extraction(user_input)
        state["current_step"] = f"Product extraction error (using fallback): {str(e)}"
    
    return state


def fallback_product_extraction(query: str, llm_response: str) -> list:
    """
    Fallback method to extract products from LLM response text
    """
    products = []
    
    # Try to find quoted strings
    quoted_items = re.findall(r'["\']([^"\']+)["\']', llm_response)
    if quoted_items:
        products = quoted_items
    else:
        # Try to extract from list format (bullet points, numbers, etc.)
        lines = [line.strip() for line in llm_response.split('\n') if line.strip()]
        for line in lines:
            # Remove common list prefixes
            cleaned = re.sub(r'^[-*•\d.)\]]\s*', '', line)
            if cleaned and len(cleaned) > 2:
                products.append(cleaned)
    
    return [p for p in products if p][:5]  # Limit to 5 products


def regex_product_extraction(query: str) -> list:
    """
    Regex-based product extraction as ultimate fallback
    """
    products = []
    query_lower = query.lower()
    
    # Common comparison patterns
    patterns = [
        r'([\w\s]+?)\s+(?:vs\.?|versus)\s+([\w\s]+?)(?:\s|$)',  # "X vs Y"
        r'compare\s+([\w\s]+?)\s+(?:and|with|to)\s+([\w\s]+?)(?:\s|$)',  # "compare X and Y"
        r'(?:difference|diff)\s+between\s+([\w\s]+?)\s+and\s+([\w\s]+?)(?:\s|$)',  # "difference between X and Y"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            for match in matches:
                for item in match:
                    cleaned = item.strip()
                    if cleaned and len(cleaned) > 2:
                        products.append(cleaned)
            break
    
    # If still no products, try to extract brand names and models
    if not products:
        products = extract_brand_models(query)
    
    return products[:5]  # Limit to 5 products


def extract_brand_models(query: str) -> list:
    """
    Extract products by identifying brand names and associated models
    """
    products = []
    
    # Common tech brands and their patterns
    brand_patterns = [
        (r'(iPhone\s*\d+\s*(?:Pro|Plus|Max)?)', 'iPhone'),
        (r'(Galaxy\s*S\d+\s*(?:Ultra|Plus)?)', 'Samsung'),
        (r'(Pixel\s*\d+\s*(?:Pro|XL)?)', 'Google'),
        (r'(MacBook\s*(?:Air|Pro)\s*M?\d*)', 'Apple'),
        (r'(Dell\s*XPS\s*\d+)', 'Dell'),
        (r'(HP\s*\w+\s*\w+)', 'HP'),
        (r'(ThinkPad\s*\w+\s*\d*)', 'Lenovo'),
        (r'(Surface\s*(?:Pro|Laptop|Book)\s*\d*)', 'Microsoft'),
        (r'(PlayStation\s*\d+|PS\d+)', 'Sony'),
        (r'(Xbox\s*(?:Series\s*)?[XS])', 'Microsoft'),
        (r'(AirPods\s*(?:Pro|Max)?)', 'Apple'),
        (r'(Galaxy\s*Watch\s*\d*)', 'Samsung'),
        (r'(Apple\s*Watch\s*(?:Series\s*)?\d*)', 'Apple'),
    ]
    
    for pattern, brand in brand_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        for match in matches:
            products.append(match.strip())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_products = []
    for p in products:
        p_lower = p.lower()
        if p_lower not in seen:
            seen.add(p_lower)
            unique_products.append(p)
    
    return unique_products


def enhanced_extraction(query: str) -> list:
    """
    Enhanced extraction combining multiple methods
    """
    # Try regex first
    products = regex_product_extraction(query)
    
    # If we have products, return them
    if len(products) >= 2:
        return products
    
    # Try brand model extraction
    brand_products = extract_brand_models(query)
    
    # Combine and deduplicate
    all_products = products + [p for p in brand_products if p not in products]
    
    return all_products[:5]  # Limit to 5 products