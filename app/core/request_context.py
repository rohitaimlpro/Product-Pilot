"""
Per-request context storage using Python contextvars.
Allows request_id to flow through logs without being passed explicitly.
"""
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def new_request_id() -> str:
    rid = str(uuid.uuid4())[:8]
    request_id_var.set(rid)
    return rid
