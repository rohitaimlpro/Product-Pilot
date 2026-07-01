"""
Unit tests for the product recommendation system.
External APIs (SerpAPI, Gemini) are mocked — no real network calls made.
Run with: pytest tests/
"""
import pytest
from unittest.mock import patch, MagicMock


# ── has_data ──────────────────────────────────────────────────────────────────

from nodes.supervisor_agent import has_data

def test_has_data_empty_list():
    assert has_data([]) is False

def test_has_data_none():
    assert has_data(None) is False

def test_has_data_with_product_info():
    data = [{"product": "iPhone 15", "info": [{"snippet": "A16 Bionic chip"}]}]
    assert has_data(data) is True

def test_has_data_with_prices():
    data = [{"product": "iPhone 15", "prices": [{"price": "₹79,900"}]}]
    assert has_data(data) is True

def test_has_data_with_reviews():
    data = [{"reviews": {"positive_reviews": ["Great camera"], "negative_reviews": []}}]
    assert has_data(data) is True

def test_has_data_empty_inner_lists():
    data = [{"product": "iPhone 15", "info": [], "prices": [], "ratings": []}]
    assert has_data(data) is False


# ── reflect_on_quality ────────────────────────────────────────────────────────

from nodes.supervisor_agent import reflect_on_quality

def test_reflect_good_product_info_high():
    state = {"product_info": [{"info_quality": "high", "info": [{"snippet": "test"}]}]}
    assert reflect_on_quality(state, "product_info_agent") == "good"

def test_reflect_good_product_info_medium():
    state = {"product_info": [{"info_quality": "medium", "info": []}]}
    assert reflect_on_quality(state, "product_info_agent") == "good"

def test_reflect_poor_product_info_low():
    state = {"product_info": [{"info_quality": "low", "info": []}]}
    assert reflect_on_quality(state, "product_info_agent") == "poor"

def test_reflect_poor_empty_product_info():
    state = {"product_info": []}
    assert reflect_on_quality(state, "product_info_agent") == "poor"

def test_reflect_good_price_medium():
    state = {"price_data": [{"price_confidence": "medium", "prices": []}]}
    assert reflect_on_quality(state, "price_agent") == "good"

def test_reflect_poor_price_low():
    state = {"price_data": [{"price_confidence": "low", "prices": []}]}
    assert reflect_on_quality(state, "price_agent") == "poor"

def test_reflect_good_review():
    state = {"review_data": [{"reviews": {"review_confidence": "high"}}]}
    assert reflect_on_quality(state, "review_agent") == "good"

def test_reflect_good_rating():
    state = {"platform_rating_data": [{"rating_confidence": "medium"}]}
    assert reflect_on_quality(state, "rating_agent") == "good"


# ── estimate_price_quality ────────────────────────────────────────────────────

from nodes.price_agent import estimate_price_quality

def test_price_quality_empty():
    confidence, price_range = estimate_price_quality([])
    assert confidence == "low"
    assert price_range is None

def test_price_quality_high_three_prices():
    prices = [{"price": "₹79,900"}, {"price": "₹80,500"}, {"price": "₹78,000"}]
    confidence, price_range = estimate_price_quality(prices)
    assert confidence == "high"
    assert price_range["min_price"] == 78000
    assert price_range["max_price"] == 80500

def test_price_quality_medium_two_prices():
    prices = [{"price": "₹79,900"}, {"price": "₹80,500"}]
    confidence, _ = estimate_price_quality(prices)
    assert confidence == "medium"

def test_price_quality_low_no_numeric():
    prices = [{"price": "Contact seller"}, {"price": "N/A"}]
    confidence, price_range = estimate_price_quality(prices)
    assert confidence == "low"
    assert price_range is None


# ── estimate_info_quality ─────────────────────────────────────────────────────

from nodes.product_info_agent import estimate_info_quality

def test_info_quality_empty():
    assert estimate_info_quality([]) == "low"

def test_info_quality_high_many_keywords():
    snippets = [{"snippet": "The camera and battery performance with display processor specifications features"}]
    assert estimate_info_quality(snippets) == "high"

def test_info_quality_medium_some_keywords():
    snippets = [{"snippet": "Good camera and battery life"}]
    assert estimate_info_quality(snippets) == "medium"

def test_info_quality_low_no_keywords():
    snippets = [{"snippet": "Buy now limited stock available"}]
    assert estimate_info_quality(snippets) == "low"


# ── agent nodes with no products ──────────────────────────────────────────────

def test_price_agent_no_products():
    from nodes.price_agent import price_agent_node
    result = price_agent_node({"products": [], "search_hints": {}})
    assert result["price_data"] == []
    assert result["price_available"] is False

def test_product_info_agent_no_products():
    from nodes.product_info_agent import product_info_agent_node
    result = product_info_agent_node({"products": [], "search_hints": {}})
    assert result["product_info"] == []
    assert result["info_available"] is False

def test_review_agent_no_products():
    from nodes.review_agent import review_rating_agent_node
    result = review_rating_agent_node({"products": [], "search_hints": {}})
    assert result["review_data"] == []
    assert result["review_available"] is False

def test_rating_agent_no_products():
    from nodes.rating_agent import rating_platform_agent_node
    result = rating_platform_agent_node({"products": [], "search_hints": {}})
    assert result["platform_rating_data"] == []
    assert result["rating_available"] is False


# ── supervisor with no products ───────────────────────────────────────────────

def test_supervisor_no_products():
    from nodes.supervisor_agent import supervisor_agent_node
    state = {
        "products": [], "agent_plan": [], "agents_executed": [],
        "product_info": [], "price_data": [], "review_data": [],
        "platform_rating_data": [], "search_hints": {}
    }
    result = supervisor_agent_node(state)
    assert result["collection_complete"] is True


# ── search_hints are passed to agents ────────────────────────────────────────

def test_price_agent_uses_search_hints():
    from nodes.price_agent import price_agent_node
    with patch("nodes.price_agent.fetch_price_results") as mock_fetch:
        mock_fetch.return_value = []
        state = {
            "products": ["iPhone 15"],
            "search_hints": {"iPhone 15": "Apple iPhone 15 128GB price India 2024"}
        }
        price_agent_node(state)
        mock_fetch.assert_called_once_with("Apple iPhone 15 128GB price India 2024")

def test_product_info_agent_uses_search_hints():
    from nodes.product_info_agent import product_info_agent_node
    with patch("nodes.product_info_agent.fetch_product_info_snippets") as mock_fetch:
        mock_fetch.return_value = []
        state = {
            "products": ["Samsung S24"],
            "search_hints": {"Samsung S24": "Samsung Galaxy S24 specifications India"}
        }
        product_info_agent_node(state)
        mock_fetch.assert_called_once_with("Samsung Galaxy S24 specifications India")

def test_agent_falls_back_to_product_name_when_no_hints():
    from nodes.price_agent import price_agent_node
    with patch("nodes.price_agent.fetch_price_results") as mock_fetch:
        mock_fetch.return_value = []
        state = {"products": ["OnePlus 12"], "search_hints": {}}
        price_agent_node(state)
        mock_fetch.assert_called_once_with("OnePlus 12")
