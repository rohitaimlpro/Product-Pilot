# test_api_complete.py - Run this to diagnose the issue
from dotenv import load_dotenv
import os
import requests

print("="*80)
print("COMPREHENSIVE API TEST")
print("="*80)

# Test 1: Environment Loading
print("\n1. TESTING ENVIRONMENT VARIABLE LOADING")
print("-"*80)
load_dotenv()
serp_key = os.getenv('SERP_API_KEY')
google_key = os.getenv('GOOGLE_API_KEY')

print(f"SERP_API_KEY loaded: {bool(serp_key)}")
print(f"GOOGLE_API_KEY loaded: {bool(google_key)}")

if serp_key:
    print(f"SERP key preview: {serp_key[:20]}...")
else:
    print("ERROR: SERP_API_KEY not found!")
    exit(1)

# Test 2: Check API Quota
print("\n2. CHECKING SERPAPI ACCOUNT STATUS")
print("-"*80)
account_url = "https://serpapi.com/account"
try:
    response = requests.get(account_url, params={"api_key": serp_key})
    account_data = response.json()
    print(f"Account status: {response.status_code}")
    print(f"Searches this month: {account_data.get('total_searches_this_month', 'N/A')}")
    print(f"Plan: {account_data.get('plan_name', 'N/A')}")
    print(f"Rate limit: {account_data.get('rate_limit_per_hour', 'N/A')} per hour")
except Exception as e:
    print(f"Could not check account: {e}")

# Test 3: Single API Call
print("\n3. TESTING SINGLE API CALL")
print("-"*80)
url = "https://serpapi.com/search"
params = {
    "engine": "google_shopping",
    "q": "iPhone 15",
    "hl": "en",
    "gl": "IN",
    "api_key": serp_key
}

print(f"Making request to: {url}")
print(f"Query: iPhone 15")

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        
        if "shopping_results" in data:
            print(f"Shopping results found: {len(data['shopping_results'])}")
            if data['shopping_results']:
                first = data['shopping_results'][0]
                print(f"\nFirst result:")
                print(f"  Title: {first.get('title', 'N/A')}")
                print(f"  Price: {first.get('price', 'N/A')}")
                print(f"  Source: {first.get('source', 'N/A')}")
        else:
            print("NO shopping_results in response")
            print(f"Full response: {data}")
    
    elif response.status_code == 429:
        print("ERROR: Rate limit exceeded!")
        print("You've hit the API rate limit. Wait before trying again.")
    
    elif response.status_code == 401:
        print("ERROR: Invalid API key!")
        
    else:
        print(f"ERROR: Unexpected status code")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"Request failed: {e}")

# Test 4: Check if agents can import
print("\n4. TESTING AGENT IMPORTS")
print("-"*80)
try:
    from nodes.price_agent import price_agent_node
    print("price_agent imported successfully")
except Exception as e:
    print(f"Failed to import price_agent: {e}")

try:
    from nodes.review_agent import review_rating_agent_node
    print("review_agent imported successfully")
except Exception as e:
    print(f"Failed to import review_agent: {e}")

try:
    from nodes.product_info_agent import product_info_agent_node
    print("product_info_agent imported successfully")
except Exception as e:
    print(f"Failed to import product_info_agent: {e}")

try:
    from nodes.rating_agent import rating_platform_agent_node
    print("rating_agent imported successfully")
except Exception as e:
    print(f"Failed to import rating_agent: {e}")

# Test 5: Test agent directly
print("\n5. TESTING PRICE AGENT DIRECTLY")
print("-"*80)
try:
    from nodes.price_agent import price_agent_node
    
    test_state = {
        "products": ["iPhone 15"],
        "price_data": [],
        "review_data": [],
        "product_info": [],
        "platform_rating_data": []
    }
    
    result = price_agent_node(test_state)
    print(f"Agent returned: {result.get('current_step')}")
    
    price_data = result.get('price_data', [])
    if price_data:
        print(f"Price data items: {len(price_data)}")
        if price_data[0].get('prices'):
            print(f"First product has {len(price_data[0]['prices'])} prices")
            print(f"Sample: {price_data[0]['prices'][0]}")
        else:
            print("WARNING: price_data structure exists but prices array is empty")
    else:
        print("ERROR: No price_data returned")
        
except Exception as e:
    print(f"Agent test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)