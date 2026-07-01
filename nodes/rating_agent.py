import os
import logging

from app.core.http_client import cached_get

logger = logging.getLogger(__name__)

SERP_URL = "https://serpapi.com/search"


def fetch_platform_ratings(query: str, max_results: int = 3) -> list:
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
        ratings_info = []
        if "shopping_results" in data:
            for item in data["shopping_results"][:max_results]:
                ratings_info.append({
                    "platform": item.get("source", "Unknown Store"),
                    "title": item.get("title", ""),
                    "rating": item.get("rating", "N/A"),
                    "total_reviews": item.get("reviews", "N/A"),
                    "platform_url": item.get("link", ""),
                })
        logger.info("Found %d ratings for: %s", len(ratings_info), query)
        return ratings_info

    except Exception as e:
        logger.error("Rating fetch error for %s: %s", query, e)
        return []


def estimate_rating_quality(ratings: list) -> tuple:
    if not ratings:
        return "low", None
    numeric_ratings = []
    for r in ratings:
        try:
            numeric_ratings.append(float(r.get("rating")))
        except (TypeError, ValueError):
            continue
    if not numeric_ratings:
        return "low", None
    avg = round(sum(numeric_ratings) / len(numeric_ratings), 2)
    confidence = (
        "high" if len(numeric_ratings) >= 3
        else "medium" if len(numeric_ratings) >= 2
        else "low"
    )
    return confidence, avg


def rating_platform_agent_node(state: dict) -> dict:
    product_names = state.get("products", [])

    if not product_names:
        logger.warning("No products provided for rating collection")
        return {**state, "platform_rating_data": [], "rating_available": False,
                "current_step": "No products for rating collection"}

    try:
        platform_ratings = []
        for product in product_names[:3]:
            search_query = state.get("search_hints", {}).get(product, product)
            logger.info("Fetching ratings for: %s", search_query)
            ratings = fetch_platform_ratings(search_query)
            confidence, avg_rating = estimate_rating_quality(ratings)
            platform_ratings.append({
                "product": product,
                "ratings": ratings,
                "rating_confidence": confidence,
                "average_rating": avg_rating,
            })

        overall_confidence = (
            "high" if any(p["rating_confidence"] == "high" for p in platform_ratings)
            else "medium" if any(p["rating_confidence"] == "medium" for p in platform_ratings)
            else "low"
        )
        logger.info("Rating data collected (%s confidence)", overall_confidence)
        return {**state, "platform_rating_data": platform_ratings, "rating_available": True,
                "rating_confidence": overall_confidence,
                "current_step": f"Rating data collected ({overall_confidence})"}

    except Exception as e:
        logger.error("Rating collection failed: %s", e)
        return {**state, "platform_rating_data": [], "rating_available": False,
                "current_step": f"Rating collection failed: {e}"}
