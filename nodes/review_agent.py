import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.http_client import cached_get

logger = logging.getLogger(__name__)

SERP_URL = "https://serpapi.com/search"

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    return _llm


def fetch_review_snippets(query: str) -> list:
    SERP_API_KEY = os.getenv("SERP_API_KEY")
    if not SERP_API_KEY:
        logger.error("SERP_API_KEY not set")
        return []

    params = {
        "engine": "google",
        "q": query + " user reviews experience",
        "hl": "en",
        "gl": "IN",
        "api_key": SERP_API_KEY,
    }

    try:
        data = cached_get(SERP_URL, params)
        snippets = []
        if "organic_results" in data:
            for result in data["organic_results"][:5]:
                snippet = result.get("snippet", "")
                if snippet:
                    snippets.append(snippet)
        logger.info("Found %d review snippets for: %s", len(snippets), query)
        return snippets

    except Exception as e:
        logger.error("Review fetch error for %s: %s", query, e)
        return []


def classify_reviews_with_llm(snippets: list, llm) -> dict:
    if not snippets:
        return {"positive_reviews": [], "negative_reviews": [],
                "review_sentiment": "unknown", "review_confidence": "low"}

    try:
        combined = "\n---\n".join(snippets[:5])
        prompt = f"""Analyze these product review snippets.

{combined}

Return strictly:

POSITIVE:
- points

NEGATIVE:
- points"""

        result = llm.invoke(prompt)
        text = result.content if hasattr(result, "content") else str(result)

        positive_reviews, negative_reviews = [], []

        if "POSITIVE:" in text:
            pos_section = text.split("POSITIVE:")[1].split("NEGATIVE:")[0]
            positive_reviews = [
                line.strip("- ").strip()
                for line in pos_section.split("\n")
                if line.strip().startswith("-")
            ][:3]

        if "NEGATIVE:" in text:
            neg_section = text.split("NEGATIVE:")[1]
            negative_reviews = [
                line.strip("- ").strip()
                for line in neg_section.split("\n")
                if line.strip().startswith("-")
            ][:3]

        total = len(positive_reviews) + len(negative_reviews)
        sentiment = (
            "positive" if len(positive_reviews) > len(negative_reviews)
            else "negative" if len(negative_reviews) > len(positive_reviews)
            else "mixed"
        )
        confidence = "high" if total >= 4 else "medium" if total >= 2 else "low"

        return {"positive_reviews": positive_reviews, "negative_reviews": negative_reviews,
                "review_sentiment": sentiment, "review_confidence": confidence}

    except Exception as e:
        logger.error("Review classification error: %s", e)
        return {"positive_reviews": [], "negative_reviews": [],
                "review_sentiment": "unknown", "review_confidence": "low"}


def review_rating_agent_node(state: dict) -> dict:
    product_names = state.get("products", [])

    if not product_names:
        logger.warning("No products provided for review collection")
        return {**state, "review_data": [], "review_available": False,
                "current_step": "No products for review collection"}

    try:
        llm = get_llm()
        review_data = []
        for product in product_names[:3]:
            search_query = state.get("search_hints", {}).get(product, product)
            logger.info("Fetching reviews for: %s", search_query)
            snippets = fetch_review_snippets(search_query)
            classified = classify_reviews_with_llm(snippets, llm)
            review_data.append({"product": product, "reviews": classified})

        logger.info("Review data collected for %d products", len(review_data))
        return {**state, "review_data": review_data, "review_available": True,
                "current_step": f"Review data collected for {len(review_data)} products"}

    except Exception as e:
        logger.error("Review collection failed: %s", e)
        return {**state, "review_data": [], "review_available": False,
                "current_step": f"Review collection failed: {e}"}
