import re
import logging

logger = logging.getLogger(__name__)

_INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|your)\s+instructions",
    r"disregard\s+(previous|all|your)\s+instructions",
    r"forget\s+(previous|all|your)\s+(instructions|rules)",
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(if\s+you\s+are|a\s+)?",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"(what|show me)\s+(are\s+)?your\s+(system\s+)?instructions",
    r"system\s+prompt",
    r"jailbreak",
    r"dan\s+mode",
    r"pretend\s+you\s+(are|have\s+no)",
    r"override\s+(your\s+)?(previous\s+)?instructions",
]


def check_input(user_input: str) -> tuple[bool, str]:
    """
    Checks user input for prompt injection attempts.
    Returns (is_safe, reason). is_safe=True means input passed all checks.
    """
    if not user_input or not user_input.strip():
        return False, "Empty query"

    lower = user_input.lower()
    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, lower):
            logger.warning("Prompt injection detected | pattern=%s | input=%s", pattern, user_input[:120])
            return False, "Query contains disallowed content"

    return True, ""
