import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

# Force UTF-8 output so non-ASCII characters (e.g. ₹ from SerpAPI) don't crash the logging handler
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from app.core.request_context import request_id_var


class RequestIdFilter(logging.Filter):
    """Injects request_id into every log record for traceability."""
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] [req:%(request_id)s] %(name)s: %(message)s"
))
handler.addFilter(RequestIdFilter())
logging.root.setLevel(logging.INFO)
logging.root.handlers = [handler]

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api.routes import router, limiter

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")

app = FastAPI(
    title="ProductPilot API",
    description="Multi-agent product recommendation and comparison system",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(router, prefix="/api")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
