from fastapi import APIRouter, HTTPException
from app.core.workflow import create_workflow
from app.models.graph_state import GraphState
from app.core.logger import DebugLogger
import traceback

router = APIRouter()
workflow = create_workflow()
logger = DebugLogger()

@router.post("/query")
def process_query(payload: dict):
    user_input = payload.get("query", "").strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        logger.clear()
        logger.log("START", "New query received", {"query": user_input})

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
            missing_data=[]
        )

        result = workflow.invoke(initial_state)
        recommendation = result.get("final_recommendation", "No recommendation generated.")

        logger.log("RESULT", "Final recommendation", {"recommendation": recommendation})

        return {
            "success": True,
            "recommendation": recommendation,
            "debug_logs": logger.get_logs()
        }

    except Exception as e:
        logger.log("ERROR", str(e), {"traceback": traceback.format_exc()})
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug")
def get_debug_logs():
    return {"logs": logger.get_logs()}
