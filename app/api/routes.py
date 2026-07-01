import asyncio
import logging
import traceback

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


@router.get("/health")
def health():
    return {"status": "ok"}


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

    # Per-request logger — no shared state between concurrent requests
    debug_logger = DebugLogger()

    try:
        logger.info("Query received: %s", user_input[:100])
        debug_logger.log("START", "New query received", {"query": user_input, "request_id": request_id})

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

        # Run blocking LangGraph workflow in thread pool — frees event loop for other requests
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, workflow.invoke, initial_state)

        recommendation = result.get("final_recommendation", "No recommendation generated.")

        logger.info("Query complete. Confidence: %s/10", result.get("confidence_score", "N/A"))
        debug_logger.log("RESULT", "Final recommendation", {"recommendation": recommendation})

        return {
            "success": True,
            "recommendation": recommendation,
            "debug_logs": debug_logger.get_logs()
        }

    except Exception as e:
        logger.error("Query failed: %s", str(e), exc_info=True)
        debug_logger.log("ERROR", str(e), {"traceback": traceback.format_exc()})
        raise HTTPException(status_code=500, detail=str(e))
