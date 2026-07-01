import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from nodes.product_info_agent import product_info_agent_node
from nodes.price_agent import price_agent_node
from nodes.review_agent import review_rating_agent_node
from nodes.rating_agent import rating_platform_agent_node

logger = logging.getLogger(__name__)

_llm = None

def get_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    return _llm

AGENT_MAP = {
    "product_info_agent": product_info_agent_node,
    "price_agent": price_agent_node,
    "review_agent": review_rating_agent_node,
    "rating_agent": rating_platform_agent_node,
}

# The specific state key each agent writes its output to
AGENT_OUTPUT_KEYS = {
    "product_info_agent": "product_info",
    "price_agent": "price_data",
    "review_agent": "review_data",
    "rating_agent": "platform_rating_data",
}


def log_message(step: str, message: str, data=None) -> None:
    logger.info("%s: %s", step, message)
    if data:
        logger.debug("  Data: %s", data)


def has_data(data):
    if not data:
        return False
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                if item.get("info"):
                    return True
                if item.get("prices"):
                    return True
                if item.get("ratings"):
                    return True
                reviews = item.get("reviews")
                if isinstance(reviews, dict):
                    if reviews.get("positive_reviews") or reviews.get("negative_reviews"):
                        return True
    return False


# ── PLAN: query-aware agent selection ──

def create_execution_plan(state: dict) -> list:
    """
    One LLM call reads the user's actual query and selects the MINIMUM
    set of agents needed. Fewer agents = faster response.
    """
    prompt = f"""You are a product research supervisor. Pick only the agents this query actually needs — fewer is better.

User query: "{state.get("input")}"
Products: {state.get("products")}

Agents available:
- product_info_agent → specs, features, display, chipset, camera, battery, storage
- price_agent        → current retail prices from stores
- review_agent       → user reviews, pros/cons, real-world experience
- rating_agent       → platform ratings and review counts

Selection rules — use the MINIMUM set:
- "affordable" / "price" / "cheaper" / "cost" / "budget" / "under X"  → ["price_agent"]
- "specs" / "features" / "display" / "camera" / "battery" / "compare specs" → ["product_info_agent"]
- "reviews" / "experience" / "reliable" / "worth it" / "problems"     → ["review_agent"]
- "rated" / "popular" / "best rated" / "rating"                       → ["rating_agent"]
- price + specs needed together                                        → ["price_agent", "product_info_agent"]
- reviews + ratings needed together                                    → ["review_agent", "rating_agent"]
- broad "compare X vs Y" with no specific angle                        → ["product_info_agent", "price_agent", "review_agent", "rating_agent"]
- broad recommendation with no specific angle                          → ["product_info_agent", "price_agent", "review_agent", "rating_agent"]

Do NOT add extra agents just because they might be useful. Match the query intent exactly.

Respond with ONLY a JSON array. Examples:
- "which is cheaper" → ["price_agent"]
- "compare specs" → ["product_info_agent"]
- "which has better reviews and ratings" → ["review_agent", "rating_agent"]
- "compare iPhone 15 vs S24" → ["product_info_agent", "price_agent", "review_agent", "rating_agent"]"""

    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        start, end = content.find("["), content.rfind("]") + 1
        if start >= 0 and end > start:
            plan = json.loads(content[start:end])
            valid = [a for a in plan if a in AGENT_MAP]
            if len(valid) >= 1:
                return valid
    except Exception as e:
        log_message("PLAN_ERROR", str(e))

    return ["product_info_agent", "price_agent", "review_agent", "rating_agent"]


# ── OBSERVE: rule-based reflection using agent confidence signals ──

def reflect_on_quality(state: dict, agent_name: str) -> str:
    """No LLM call — reads confidence signals already computed by each agent."""
    if agent_name == "product_info_agent":
        for item in state.get("product_info", []):
            if item.get("info_quality") in ("high", "medium"):
                return "good"

    elif agent_name == "price_agent":
        for item in state.get("price_data", []):
            if item.get("price_confidence") in ("high", "medium"):
                return "good"

    elif agent_name == "review_agent":
        for item in state.get("review_data", []):
            reviews = item.get("reviews", {})
            if reviews.get("review_confidence") in ("high", "medium"):
                return "good"

    elif agent_name == "rating_agent":
        for item in state.get("platform_rating_data", []):
            if item.get("rating_confidence") in ("high", "medium"):
                return "good"

    return "poor"


# ── REFORMULATE: LLM generates better queries on poor results ──

def reformulate_queries(state: dict, agent_name: str) -> dict:
    """Single LLM call triggered only when reflect_on_quality returns 'poor'."""
    products = state.get("products", [])

    purpose = {
        "product_info_agent": "product specifications and features",
        "price_agent": "current retail price in India",
        "review_agent": "user reviews and real-world experience",
        "rating_agent": "platform ratings and review counts",
    }.get(agent_name, "product information")

    prompt = f"""Search for {purpose} returned no useful results for: {products}

Generate a more specific search query for each product.

Respond ONLY with a JSON object mapping each product to an improved query.
Example: {{"iPhone 15": "Apple iPhone 15 128GB price India 2024"}}"""

    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        start, end = content.find("{"), content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception as e:
        log_message("REFORMULATE_ERROR", str(e))

    return {p: f"{p} India 2024 {purpose}" for p in products}


# ── CONFIDENCE: LLM scores data sufficiency 1-10 ──

def get_confidence_score(state: dict) -> int:
    """Called once after all agents finish to decide if more data is needed."""
    prompt = f"""Rate your confidence (1-10) in making a product recommendation with this data:

Products: {state.get("products")}
Agents already run: {state.get("agents_executed", [])}
Product info quality: {[i.get("info_quality") for i in state.get("product_info", [])]}
Price confidence: {[i.get("price_confidence") for i in state.get("price_data", [])]}
Review confidence: {[i.get("reviews", {}).get("review_confidence") for i in state.get("review_data", [])]}

8-10: enough data to recommend confidently
5-7: borderline, more data would help
1-4: major gaps

Respond ONLY with a single integer 1-10."""

    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        digits = "".join(filter(str.isdigit, response.content.strip()))
        score = int(digits[:2]) if digits else 5
        return min(max(score, 1), 10)
    except:
        return 5


# ── RUN AGENT WITH REFLECT + RETRY ──

def run_agent_with_reflection(state: dict, agent_name: str) -> dict:
    """
    ACT → OBSERVE → REFORMULATE + RETRY if quality is poor.
    One retry max per agent. Safe to call from multiple threads —
    each call receives its own state copy.
    """
    agent_func = AGENT_MAP[agent_name]

    log_message("AGENT_START", f"Running {agent_name}")
    result = agent_func(state)
    state = {**state, **result}
    time.sleep(0.3)

    quality = reflect_on_quality(state, agent_name)
    log_message("REFLECT", f"{agent_name} quality: {quality}")

    if quality == "poor":
        log_message("REFORMULATE", f"Poor results — generating better queries for {agent_name}")
        hints = reformulate_queries(state, agent_name)
        log_message("REFORMULATE", f"New queries: {hints}")

        state["search_hints"] = hints
        result = agent_func(state)
        state = {**state, **result}
        state["search_hints"] = {}
        time.sleep(0.3)

        log_message("REFLECT", f"{agent_name} quality after retry: {reflect_on_quality(state, agent_name)}")

    return state


# ── SUPERVISOR NODE ──

def supervisor_agent_node(state: dict) -> dict:
    """
    Agentic supervisor with three phases:

    Phase 1 — PLAN (one LLM call):
        Reads the user's query and selects which agents to run.

    Phase 2 — EXECUTE (parallel):
        All planned agents run simultaneously via ThreadPoolExecutor.
        Each agent still has its own ACT → OBSERVE → REFLECT cycle.
        Wall-clock time = slowest single agent, not sum of all agents.

    Phase 3 — FINISH (one LLM call):
        Confidence check. Adds rating_agent if score < 7 and it wasn't in the plan.
    """
    try:
        products = state.get("products", [])

        if not products:
            return {**state, "collection_complete": True, "current_step": "No products found"}

        # ── PHASE 1: PLAN ──
        log_message("SUPERVISOR", "Building execution plan", {
            "query": state.get("input"),
            "products": products,
        })
        agent_plan = create_execution_plan(state)
        log_message("SUPERVISOR_PLAN", f"Query-aware plan: {agent_plan}")

        # ── PHASE 2: PARALLEL EXECUTE ──
        log_message("SUPERVISOR", f"Running {len(agent_plan)} agents in parallel")

        agent_results: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=len(agent_plan)) as executor:
            future_to_agent = {
                executor.submit(run_agent_with_reflection, dict(state), agent_name): agent_name
                for agent_name in agent_plan
            }
            for future in as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    agent_results[agent_name] = future.result()
                    log_message("AGENT_DONE", f"{agent_name} finished")
                except Exception as e:
                    log_message("AGENT_ERROR", f"{agent_name} failed: {e}")
                    agent_results[agent_name] = state

        # Merge: each agent writes to its own output key — no conflicts
        merged = dict(state)
        for agent_name in agent_plan:
            if agent_name in agent_results:
                key = AGENT_OUTPUT_KEYS[agent_name]
                merged[key] = agent_results[agent_name].get(key, [])

        agents_executed = list(agent_results.keys())
        merged["agent_plan"] = agent_plan
        merged["agents_executed"] = agents_executed

        # ── PHASE 3: CONFIDENCE CHECK ──
        log_message("SUPERVISOR", "Scoring data confidence")
        confidence = get_confidence_score(merged)
        log_message("CONFIDENCE", f"Score: {confidence}/10")

        if confidence < 7 and "rating_agent" not in agents_executed:
            log_message("SUPERVISOR", f"Confidence {confidence}/10 — adding rating_agent")
            rating_result = run_agent_with_reflection(dict(merged), "rating_agent")
            merged[AGENT_OUTPUT_KEYS["rating_agent"]] = rating_result.get(AGENT_OUTPUT_KEYS["rating_agent"], [])
            agents_executed.append("rating_agent")
            merged["agents_executed"] = agents_executed
            confidence = get_confidence_score(merged)
            log_message("CONFIDENCE", f"Score after ratings: {confidence}/10")

        return {
            **merged,
            "collection_complete": True,
            "confidence_score": confidence,
            "current_step": f"Collection complete (parallel). Agents: {agents_executed}. Confidence: {confidence}/10",
        }

    except Exception as e:
        log_message("SUPERVISOR_ERROR", str(e))
        import traceback
        traceback.print_exc()
        return {**state, "collection_complete": True, "current_step": f"Supervisor error: {str(e)}"}
