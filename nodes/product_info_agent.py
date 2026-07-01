import os
import logging

from app.core.http_client import cached_get

logger = logging.getLogger(__name__)

SERP_URL = "https://serpapi.com/search"


def fetch_product_info_snippets(query: str, max_results: int = 3) -> list:
    SERP_API_KEY = os.getenv("SERP_API_KEY")
    if not SERP_API_KEY:
        logger.error("SERP_API_KEY not set")
        return []

    params = {
        "engine": "google",
        "q": query + " specifications features overview",
        "hl": "en",
        "gl": "IN",
        "api_key": SERP_API_KEY,
    }

    try:
        data = cached_get(SERP_URL, params)
        snippets = []
        if "organic_results" in data:
            for result in data["organic_results"][:max_results]:
                snippet = result.get("snippet", "")
                if snippet:
                    snippets.append({
                        "title": result.get("title", "").strip(),
                        "snippet": snippet.strip(),
                        "link": result.get("link", ""),
                    })
        logger.info("Found %d info snippets for: %s", len(snippets), query)
        return snippets

    except Exception as e:
        logger.error("Error fetching product info for %s: %s", query, e)
        return []


def estimate_info_quality(snippets: list) -> str:
    if not snippets:
        return "low"
    combined = " ".join(s["snippet"].lower() for s in snippets)
    keywords = ["battery", "camera", "display", "processor", "performance", "features", "specifications"]
    score = sum(1 for k in keywords if k in combined)
    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    return "low"


def product_info_agent_node(state: dict) -> dict:
    product_names = state.get("products", [])

    if not product_names:
        logger.warning("No products provided for info collection")
        return {**state, "product_info": [], "info_available": False,
                "info_quality": "low", "current_step": "No products for info collection"}

    try:
        all_info = []
        for product in product_names[:3]:
            search_query = state.get("search_hints", {}).get(product, product)
            logger.info("Fetching product info for: %s", search_query)
            snippets = fetch_product_info_snippets(search_query)
            quality = estimate_info_quality(snippets)
            all_info.append({"product": product, "info": snippets, "info_quality": quality})

        overall_quality = (
            "high" if any(p["info_quality"] == "high" for p in all_info)
            else "medium" if any(p["info_quality"] == "medium" for p in all_info)
            else "low"
        )
        logger.info("Product info collected (%s quality)", overall_quality)
        return {**state, "product_info": all_info, "info_available": True,
                "info_quality": overall_quality,
                "current_step": f"Product info collected ({overall_quality})"}

    except Exception as e:
        logger.error("Product info collection failed: %s", e)
        return {**state, "product_info": [], "info_available": False,
                "info_quality": "low", "current_step": f"Product info collection failed: {e}"}
