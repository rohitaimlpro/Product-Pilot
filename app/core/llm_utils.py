import time
import logging
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

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

    last_error = None
    for attempt in range(1, _MAX_RETRIES + 2):
        try:
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            last_error = e
            if attempt <= _MAX_RETRIES:
                logger.warning("%s attempt %d failed: %s — retrying in %ds",
                               context, attempt, e, _RETRY_DELAY)
                time.sleep(_RETRY_DELAY)
            else:
                logger.error("%s failed after %d attempts: %s", context, attempt, e)

    raise last_error
