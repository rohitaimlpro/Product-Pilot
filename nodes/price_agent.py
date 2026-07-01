import os
import re
import logging

from app.core.http_client import cached_get

logger = logging.getLogger(__name__)

SERP_URL = "https://serpapi.com/search"


def fetch_price_results(query: str, max_results: int = 3) -> list:
    SERP_API_KEY = os.getenv("SERP_API_KEY")
    if not SERP_API_KEY:
        logger.error("SERP_API_KEY not set")
        return []

    params = {
        "engine": "google_shopping",
        "q": query,
        "hl": "en",
        "gl": "IN",
        "api_key": SERP_API_KEY,
    }

    try:
        data = cached_get(SERP_URL, params)
        results = []
        if "shopping_results" in data:
            for item in data["shopping_results"][:max_results]:
                results.append({
                    "store": item.get("source", "Unknown"),
                    "title": item.get("title", "").strip(),
                    "price": item.get("price", "Not Found").strip(),
                    "url": item.get("link", ""),
                })
        logger.info("Found %d price results for: %s", len(results), query)
        return results

    except Exception as e:
        logger.error("Price fetch error for %s: %s", query, e)
        return []


def extract_numeric_price(price_text: str) -> int | None:
    if not price_text:
        return None
    match = re.search(r"[\d,]+", price_text.replace(",", ""))
    if match:
        try:
            return int(match.group().replace(",", ""))
        except ValueError:
            return None
    return None


def estimate_price_quality(price_list: list) -> tuple:
    if not price_list:
        return "low", None
    numeric_prices = [extract_numeric_price(item.get("price", "")) for item in price_list]
    numeric_prices = [p for p in numeric_prices if p]
    if not numeric_prices:
        return "low", None
    confidence = (
        "high" if len(numeric_prices) >= 3
        else "medium" if len(numeric_prices) >= 2
        else "low"
    )
    return confidence, {"min_price": min(numeric_prices), "max_price": max(numeric_prices)}


def price_agent_node(state: dict) -> dict:
    product_names = state.get("products", [])

    if not product_names:
        logger.warning("No products provided for price collection")
        return {**state, "price_data": [], "price_available": False,
                "current_step": "No products for price collection"}

    try:
        all_prices = []
        for product in product_names[:3]:
            search_query = state.get("search_hints", {}).get(product, product)
            logger.info("Fetching prices for: %s", search_query)
            prices = fetch_price_results(search_query)
            confidence, price_range = estimate_price_quality(prices)
            all_prices.append({
                "product": product,
                "prices": prices,
                "price_confidence": confidence,
                "price_range": price_range,
            })

        overall_confidence = (
            "high" if any(p["price_confidence"] == "high" for p in all_prices)
            else "medium" if any(p["price_confidence"] == "medium" for p in all_prices)
            else "low"
        )
        logger.info("Price data collected (%s confidence)", overall_confidence)
        return {**state, "price_data": all_prices, "price_available": True,
                "price_confidence": overall_confidence,
                "current_step": f"Price data collected ({overall_confidence})"}

    except Exception as e:
        logger.error("Price collection failed: %s", e)
        return {**state, "price_data": [], "price_available": False,
                "current_step": f"Price collection failed: {e}"}
