import os
import re
import json
import logging
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )


def query_parser_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Single LLM call replacing two sequential nodes (intent_classifier + product_extractor).
    Returns both intent and product list in one round-trip, saving ~2s.
    """
    user_input = state.get("input", "")

    prompt = f"""You are a query parser for a product research assistant.

From the user's query, extract TWO things and return ONLY a JSON object:

1. "intent": "comparison" if user compares 2+ specific products, else "recommendation"
2. "products": array of full product names mentioned (brand + model)

Rules:
- "compare", "vs", "versus", "difference between", "better" + 2 products → "comparison"
- "recommend", "suggest", "best", "under X price", single category → "recommendation"
- Keep full product names: "iPhone 14 Pro Max" not "iPhone"
- For recommendation queries, products may be empty []

Query: "{user_input}"

Examples:
{{"intent": "comparison", "products": ["iPhone 15", "Samsung Galaxy S24"]}}
{{"intent": "comparison", "products": ["OnePlus 12", "Pixel 8"]}}
{{"intent": "recommendation", "products": []}}

Respond with ONLY the JSON object, no explanation."""

    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        start, end = content.find("{"), content.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            intent = parsed.get("intent", "recommendation")
            products = parsed.get("products", [])

            if intent not in ("comparison", "recommendation"):
                intent = "recommendation"
            products = [str(p).strip() for p in products if p]

            # Regex fallback if LLM returned no products for a comparison query
            if intent == "comparison" and len(products) < 2:
                products = _regex_extract(user_input)

            logger.info("Query parsed — intent: %s, products: %s", intent, products)
            return {**state, "intent": intent, "products": products,
                    "current_step": f"Parsed: {intent}, {len(products)} products"}

    except Exception as e:
        logger.error("Query parser LLM failed: %s", e)

    # Full fallback — derive intent and products from keywords alone
    intent = _fallback_intent(user_input)
    products = _regex_extract(user_input)
    logger.warning("Using regex fallback — intent: %s, products: %s", intent, products)
    return {**state, "intent": intent, "products": products,
            "current_step": f"Parsed (fallback): {intent}, {len(products)} products"}


def _fallback_intent(query: str) -> str:
    comparison_keywords = ["compare", "versus", "vs", "difference between", "better than"]
    return "comparison" if any(k in query.lower() for k in comparison_keywords) else "recommendation"


def _regex_extract(query: str) -> list:
    patterns = [
        r'([\w\s]+?)\s+(?:vs\.?|versus)\s+([\w\s]+?)(?:\s|$)',
        r'compare\s+([\w\s]+?)\s+(?:and|with|to)\s+([\w\s]+?)(?:\s|$)',
        r'(?:difference|diff)\s+between\s+([\w\s]+?)\s+and\s+([\w\s]+?)(?:\s|$)',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            products = [item.strip() for match in matches for item in match if item.strip()]
            return products[:5]

    brand_patterns = [
        r'(iPhone\s*\d+\s*(?:Pro|Plus|Max)?)',
        r'(Galaxy\s*S\d+\s*(?:Ultra|Plus)?)',
        r'(Pixel\s*\d+\s*(?:Pro|XL)?)',
        r'(MacBook\s*(?:Air|Pro)\s*M?\d*)',
        r'(OnePlus\s*\d+\s*(?:Pro)?)',
        r'(Dell\s*XPS\s*\d+)',
        r'(Surface\s*(?:Pro|Laptop|Book)\s*\d*)',
        r'(PlayStation\s*\d+|PS\d+)',
        r'(Xbox\s*(?:Series\s*)?[XS])',
    ]
    products = []
    seen = set()
    for pattern in brand_patterns:
        for match in re.findall(pattern, query, re.IGNORECASE):
            p = match.strip()
            if p.lower() not in seen:
                seen.add(p.lower())
                products.append(p)
    return products[:5]
