import time
import logging
import json
from langchain_core.messages import HumanMessage
from app.core.config import LLM_PROVIDER, GEMINI_MODEL, GOOGLE_API_KEY, QWEN_MODEL, OLLAMA_BASE_URL

logger = logging.getLogger(__name__)


def get_llm(thinking_budget: int = 0, temperature: float = 0, force_provider: str = None):
    """
    Factory that returns the right LLM based on LLM_PROVIDER env var.
    - LLM_PROVIDER=gemini  → Google Gemini 2.5 Flash (default)
    - LLM_PROVIDER=qwen    → Qwen3 1.7B via local Ollama
    force_provider overrides LLM_PROVIDER for a single call (e.g. force_provider="gemini").
    thinking_budget is Gemini-only; ignored for Qwen.
    """
    provider = force_provider or LLM_PROVIDER

    if provider == "qwen":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=QWEN_MODEL, base_url=OLLAMA_BASE_URL, temperature=temperature)

    from langchain_google_genai import ChatGoogleGenerativeAI
    if thinking_budget > 0:
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=1,
            google_api_key=GOOGLE_API_KEY,
            model_kwargs={"generation_config": {"thinking_config": {"thinking_budget": thinking_budget}}}
        )
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=temperature, google_api_key=GOOGLE_API_KEY)

_MAX_RETRIES = 2
_RETRY_DELAY = 2  # seconds between retries


def invoke_with_retry(llm, messages, context: str = "LLM") -> str:
    """
    Wraps any LangChain LLM invoke with retry logic.
    Retries up to _MAX_RETRIES times on transient failures.
    Returns content string or raises on final failure.
    """
    if isinstance(messages, str):
        messages = [HumanMessage(content=messages)]

    model_name = getattr(llm, "model", type(llm).__name__)

    last_error = None
    for attempt in range(1, _MAX_RETRIES + 2):
        t0 = time.time()
        try:
            response = llm.invoke(messages)
            _audit(context, model_name, attempt, round((time.time() - t0) * 1000), True, messages)
            return response.content
        except Exception as e:
            last_error = e
            _audit(context, model_name, attempt, round((time.time() - t0) * 1000), False, messages, str(e))
            if attempt <= _MAX_RETRIES:
                logger.warning("%s attempt %d failed: %s — retrying in %ds",
                               context, attempt, e, _RETRY_DELAY)
                time.sleep(_RETRY_DELAY)
            else:
                logger.error("%s failed after %d attempts: %s", context, attempt, e)

    raise last_error


def _audit(context: str, model: str, attempt: int, latency_ms: int, success: bool, messages, error: str = None):
    input_chars = sum(len(m.content) for m in messages) if isinstance(messages, list) else len(str(messages))
    entry = {
        "audit": True,
        "context": context,
        "model": model,
        "attempt": attempt,
        "latency_ms": latency_ms,
        "input_chars": input_chars,
        "success": success,
    }
    if error:
        entry["error"] = error
    logger.info(json.dumps(entry))
