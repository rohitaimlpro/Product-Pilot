import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.core.llm_utils import invoke_with_retry
from app.core.config import GEMINI_MODEL, GOOGLE_API_KEY

logger = logging.getLogger(__name__)

_llm = None

def get_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=1,
            google_api_key=GOOGLE_API_KEY,
            model_kwargs={
                "generation_config": {
                    "thinking_config": {"thinking_budget": 512}
                }
            }
        )
    return _llm


def _run(state: dict) -> tuple[int, str]:
    """One LLM call: returns (score 1-10, reflection summary)."""
    data_summary = {
        "specs":    "available" if state.get("product_info")         else "missing",
        "prices":   "available" if state.get("price_data")           else "missing",
        "reviews":  "available" if state.get("review_data")          else "missing",
        "ratings":  "available" if state.get("platform_rating_data") else "missing",
    }

    prompt = f"""You are reviewing product research data collected to answer this query:
"{state.get("input")}"

Products: {state.get("products")}
Agents run: {state.get("agents_executed", [])}

Data collected:
- Specifications : {data_summary["specs"]}
- Prices        : {data_summary["prices"]}
- User reviews  : {data_summary["reviews"]}
- Platform ratings: {data_summary["ratings"]}

Return ONLY this JSON:
{{
  "score": <integer 1-10>,
  "reflection": "<2-3 sentences: what is well-supported and what is missing>"
}}

Score guide:
8-10 = enough data to recommend confidently
5-7  = borderline, some gaps
1-4  = major gaps, recommendation will be weak"""

    import json
    try:
        content = invoke_with_retry(get_llm(), [HumanMessage(content=prompt)], context="reflect_and_score").strip()
        start, end = content.find("{"), content.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            score = int(str(parsed.get("score", 5)).strip())
            score = max(1, min(10, score))
            reflection = str(parsed.get("reflection", "")).strip()
            return score, reflection
    except Exception as e:
        logger.error("reflect_and_score LLM failed: %s", e)

    return 5, "Reflection unavailable — proceeding with available data."


def reflect_and_score_node(state: dict) -> dict:
    """
    Replaces two sequential LLM calls (confidence check + reflection) with one.

    1. One LLM call → confidence score (1-10) + reflection summary
    2. If score < 7 and rating_agent not yet run → add it as fallback, re-score
    3. Passes analysis_context to analyzer
    """
    from nodes.supervisor_agent import run_agent_with_reflection, AGENT_OUTPUT_KEYS

    score, reflection = _run(state)
    logger.info("reflect_and_score: score=%d/10", score)

    # Fallback: add rating_agent if confidence low and it wasn't already run
    agents_executed = list(state.get("agents_executed", []))
    if score < 7 and "rating_agent" not in agents_executed:
        logger.info("Score %d/10 — adding rating_agent as fallback", score)
        fallback = run_agent_with_reflection(dict(state), "rating_agent")
        state = {
            **state,
            AGENT_OUTPUT_KEYS["rating_agent"]: fallback.get(AGENT_OUTPUT_KEYS["rating_agent"], []),
        }
        agents_executed.append("rating_agent")
        score, reflection = _run(state)
        logger.info("reflect_and_score after fallback: score=%d/10", score)

    return {
        **state,
        "agents_executed": agents_executed,
        "confidence_score": score,
        "analysis_context": reflection,
        "current_step": f"Reflect+score complete — {score}/10",
    }
