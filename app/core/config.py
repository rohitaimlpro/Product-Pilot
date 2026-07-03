import os

GEMINI_MODEL = "gemini-2.5-flash"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SERPAPI_KEY = os.getenv("SERPAPI_KEY") or os.getenv("SERP_API_KEY") or ""

# Set LLM_PROVIDER=qwen in .env to use local Qwen3 1.7B via Ollama
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" | "qwen"
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen3:1.7b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
