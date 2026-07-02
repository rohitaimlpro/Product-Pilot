import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.core.llm_utils import invoke_with_retry

from nodes.product_info_agent import product_info_agent_node
from nodes.price_agent import price_agent_node
from nodes.review_agent import review_rating_agent_node
from nodes.rating_agent import rating_platform_agent_node
from nodes.recommendation_agent import recommendation_agent_node

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


# ── PLAN: single LLM call → intent + products + agents ──

def create_execution_plan(state: dict) -> dict:
    """
    Single LLM call replacing query_parser + old planner.
    Returns intent, extracted products, and minimum agent list together.
    """
    prompt = f"""You are a product research supervisor. Analyze this query and return a single JSON object.

User query: "{state.get("input")}"

Return ONLY this JSON (no explanation):
{{
  "intent": "comparison" or "recommendation",
  "products": ["Brand Model", ...],
  "agents": ["agent1", ...]
}}

Intent rules:
- "comparison" → user mentions 2+ specific products, uses vs/compare/versus/difference/better
- "recommendation" → user wants suggestions, best X, recommend, under price, gaming laptop etc.

Product extraction:
- Keep full names: "iPhone 15 Pro Max" not "iPhone". Include brand + model.
- For recommendation queries return []

Agent selection — pick MINIMUM needed:
- price_agent        → affordable / price / cheaper / cost / budget / under X
- product_info_agent → specs / features / display / camera / battery / chipset
- review_agent       → reviews / experience / reliable / worth it / problems
- rating_agent       → rated / popular / rating / best rated
- price + specs together → both agents
- reviews + ratings together → both agents
- broad compare or recommendation (no specific angle) → all 4

Examples:
{{"intent":"comparison","products":["iPhone 15","Samsung Galaxy S24"],"agents":["price_agent"]}}
{{"intent":"comparison","products":["OnePlus 12","Pixel 8"],"agents":["product_info_agent","price_agent"]}}
{{"intent":"comparison","products":["Samsung Galaxy S24","iPhone 15"],"agents":["product_info_agent","price_agent","review_agent","rating_agent"]}}
{{"intent":"recommendation","products":[],"agents":["product_info_agent","price_agent","review_agent","rating_agent"]}}"""

    try:
        content = invoke_with_retry(get_llm(), [HumanMessage(content=prompt)], context="supervisor").strip()
        start, end = content.find("{"), content.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            intent   = parsed.get("intent", "recommendation")
            products = [str(p).strip() for p in parsed.get("products", []) if p]
            agents   = [a for a in parsed.get("agents", []) if a in AGENT_MAP]
            if not agents:
                agents = list(AGENT_MAP.keys())
            log_message("PLAN", f"intent={intent} products={products} agents={agents}")
            return {"intent": intent, "products": products, "agents": agents}
    except Exception as e:
        log_message("PLAN_ERROR", str(e))

    return {"intent": "recommendation", "products": [], "agents": list(AGENT_MAP.keys())}


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
        content = invoke_with_retry(get_llm(), [HumanMessage(content=prompt)], context="reformulate").strip()
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
        digits = "".join(filter(str.isdigit, invoke_with_retry(get_llm(), [HumanMessage(content=prompt)], context="confidence").strip()))
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
    Agentic supervisor — now the single entry point replacing query_parser.

    Phase 1 — PLAN (one LLM call):
        Detects intent, extracts products, and selects minimum agents.
        For recommendation queries, calls recommendation_agent to generate products first.

    Phase 2 — EXECUTE (parallel):
        All planned agents run simultaneously via ThreadPoolExecutor.
        Each agent still has its own ACT → OBSERVE → REFLECT cycle.
        Wall-clock time = slowest single agent, not sum of all agents.

    Phase 3 — FINISH (one LLM call):
        Confidence check. Adds rating_agent if score < 7 and it wasn't in the plan.
    """
    try:
        # ── PHASE 1: PLAN ──
        log_message("SUPERVISOR", "Parsing query and building plan", {"query": state.get("input")})
        plan = create_execution_plan(state)

        intent    = plan["intent"]
        products  = plan["products"]
        agent_plan = plan["agents"]

        state = {**state, "intent": intent}

        # For recommendation queries, generate product list first
        if intent == "recommendation" or not products:
            log_message("SUPERVISOR", "Recommendation query — generating product list")
            state = recommendation_agent_node(state)
            products = state.get("products", [])
        else:
            state = {**state, "products": products}

        if not products:
            return {**state, "collection_complete": True, "current_step": "No products found"}

        log_message("SUPERVISOR_PLAN", f"intent={intent} products={products} agents={agent_plan}")

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

        return {
            **merged,
            "collection_complete": True,
            "current_step": f"Collection complete. Agents: {agents_executed}",
        }

    except Exception as e:
        log_message("SUPERVISOR_ERROR", str(e))
        import traceback
        traceback.print_exc()
        return {**state, "collection_complete": True, "current_step": f"Supervisor error: {str(e)}"}
