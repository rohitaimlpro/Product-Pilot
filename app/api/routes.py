import os
import time
import hashlib
import asyncio
import logging
import traceback
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.workflow import create_workflow
from app.models.graph_state import GraphState
from app.core.logger import DebugLogger
from app.core.request_context import new_request_id

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()
workflow = create_workflow()

MAX_QUERY_LENGTH = 500
CACHE_TTL = 3600  # cache results for 1 hour

# In-memory response cache: query_hash → {result, timestamp}
_cache: dict = {}


def _cache_key(query: str) -> str:
    return hashlib.md5(query.lower().strip().encode()).hexdigest()


def _get_cached(query: str):
    key = _cache_key(query)
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["result"]
    return None


def _set_cache(query: str, result: dict):
    key = _cache_key(query)
    _cache[key] = {"result": result, "ts": time.time()}
    # Evict oldest entries if cache grows too large
    if len(_cache) > 500:
        oldest = sorted(_cache.items(), key=lambda x: x[1]["ts"])[:100]
        for k, _ in oldest:
            del _cache[k]


@router.get("/health")
def health():
    """Real health check — verifies env vars are set."""
    issues = []
    if not os.getenv("GOOGLE_API_KEY"):
        issues.append("GOOGLE_API_KEY not set")
    if not os.getenv("SERPAPI_KEY") and not os.getenv("SERP_API_KEY"):
        issues.append("SERPAPI_KEY not set")

    if issues:
        raise HTTPException(status_code=503, detail={"status": "degraded", "issues": issues})

    return {
        "status": "ok",
        "cache_size": len(_cache),
        "model": "gemini-2.5-flash"
    }


@router.post("/query")
@limiter.limit("10/minute")
async def process_query(request: Request, payload: dict):
    request_id = new_request_id()

    user_input = payload.get("query", "").strip()

    if not user_input:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    if len(user_input) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Query exceeds {MAX_QUERY_LENGTH} character limit."
        )

    # ── Cache hit ──
    cached = _get_cached(user_input)
    if cached:
        logger.info("Cache hit for query: %s", user_input[:60])
        return {**cached, "cached": True}

    debug_logger = DebugLogger()

    try:
        logger.info("[%s] Query received: %s", request_id, user_input[:100])

        initial_state = GraphState(
            input=user_input,
            intent="",
            products=[],
            price_data=[],
            review_data=[],
            product_info=[],
            platform_rating_data=[],
            final_recommendation="",
            current_step="",
            missing_data=[],
            collection_complete=False,
            search_hints={},
            confidence_score=0,
            analysis_context="",
            agent_plan=[],
            agents_executed=[]
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, workflow.invoke, initial_state)

        recommendation = result.get("final_recommendation", "No recommendation generated.")
        logger.info("[%s] Query complete. Confidence: %s/10", request_id, result.get("confidence_score"))

        response = {
            "success": True,
            "recommendation": recommendation,
            "agents_executed": result.get("agents_executed", []),
            "confidence_score": result.get("confidence_score", 0),
            "cached": False,
        }

        _set_cache(user_input, response)
        return response

    except Exception as e:
        logger.error("[%s] Query failed: %s", request_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
