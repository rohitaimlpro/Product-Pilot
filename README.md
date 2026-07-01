<div align="center">

# 🤖 Product Pilot — Multi-Agent AI Product Recommendation System

**An intelligent product research assistant powered by LangGraph, Google Gemini 2.5 Flash, and SerpAPI.**  
Ask in plain English. Get structured, data-backed product recommendations in seconds.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-FF6B6B?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph)
[![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-Google_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Tests](https://img.shields.io/badge/Tests-30%2F30_Passing-22C55E?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)
[![License](https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge)](LICENSE)

</div>

---

## What It Does

Type a natural language query like *"which is more affordable iPhone 14 Pro Max or iPhone 15"* or *"compare Samsung S24 vs iPhone 15"* — Product Pilot intelligently routes the query through a pipeline of specialized AI agents, fetches real-time data from the web, and returns a structured comparison with prices, specs, reviews, and ratings.

---

## System Architecture

```
╔══════════════════════════════════════════════════════════════════════╗
║                        USER QUERY (Natural Language)                 ║
╚══════════════════════════╦═══════════════════════════════════════════╝
                           │
                    ┌──────▼──────┐
                    │   Intent    │  ← Classifies: compare / recommend
                    │  Classifier │     / specs / price / reviews
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Product   │  ← Extracts product names from
                    │  Extractor  │     the raw query string
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │     SUPERVISOR AGENT    │
              │  ┌─────────────────┐    │
              │  │  PLAN (1 LLM    │    │  ← Selects MINIMUM agents
              │  │  call): picks   │    │     needed for the query
              │  │  agents needed  │    │
              │  └────────┬────────┘    │
              │           │ PARALLEL    │
              │   ┌───────┼───────┐    │
              └───┼───────┼───────┼────┘
                  │       │       │
          ┌───────▼──┐ ┌──▼───┐ ┌▼────────┐ ┌──────────┐
          │  Price   │ │ Info │ │ Review  │ │  Rating  │
          │  Agent   │ │Agent │ │  Agent  │ │  Agent   │
          │          │ │      │ │         │ │          │
          │ Prices & │ │Specs,│ │  Pros,  │ │ Platform │
          │  Deals   │ │Feats │ │  Cons,  │ │ Ratings  │
          └────┬─────┘ └──┬───┘ └───┬─────┘ └────┬─────┘
               │           │         │              │
               └───────────┴────┬────┴──────────────┘
                                │  (each agent runs ACT→OBSERVE→RETRY)
                    ┌───────────▼───────────┐
                    │    CONFIDENCE CHECK    │  ← Score < 7 triggers
                    │       (1 – 10)         │    fallback agent
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │    REFLECTION NODE     │  ← Reviews data quality
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │    ANALYZER AGENT      │  ← Synthesizes everything
                    └───────────┬───────────┘    into final answer
                                │
                    ┌───────────▼───────────┐
                    │  STRUCTURED RESPONSE   │
                    └───────────────────────┘
```

---

## Key Features

### Selective LLM Planning
The supervisor makes one LLM call to read the user's intent and selects only the agents actually needed — never more.

| Query Type | Agents Selected |
|---|---|
| `"which is more affordable?"` | `price_agent` only |
| `"compare specs and price"` | `product_info_agent` + `price_agent` |
| `"which has better reviews and ratings?"` | `review_agent` + `rating_agent` |
| `"compare X vs Y"` (broad) | All 4 agents |

### Parallel Agent Execution
All selected agents run simultaneously via `ThreadPoolExecutor`. Wall-clock time = slowest single agent, not the sum.

```
Sequential:  [price 15s] → [info 15s] → [review 15s] → [rating 15s] = 60s
Parallel:    [price 15s]
             [info  15s]  ← all run at the same time
             [review 15s]
             [rating 15s]                                             = 15s ✅
```

**Result: 4× latency reduction (60s → 15s)**

### ACT → OBSERVE → REFORMULATE → RETRY Loop
Every agent follows a self-correcting agentic cycle — not just a one-shot API call:

```
┌─────────────────────────────────────────────────────┐
│                   AGENT CYCLE                        │
│                                                      │
│  1. ACT          → Search SerpAPI for product data  │
│  2. OBSERVE      → Rule-based quality check          │
│                    (high / medium / low confidence)  │
│  3. REFORMULATE  → LLM generates better queries     │
│                    (only if quality = low)            │
│  4. RETRY        → Re-search with improved queries  │
└─────────────────────────────────────────────────────┘
```

### Confidence Scoring + Fallback
After all agents finish, an LLM scores overall data sufficiency from 1–10. If the score falls below 7, a fallback agent is automatically triggered — no manual intervention.

### Optimized Gemini Reasoning
`thinking_budget` caps prevent unbounded reasoning on large contexts:
- Analyzer node: `thinking_budget = 1024`
- Reflection node: `thinking_budget = 512`

**Result: Total response time cut from 290s → 64s**

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Agent Orchestration | LangGraph (StateGraph) | Graph-based multi-agent workflow |
| LLM | Google Gemini 2.5 Flash | Planning, reformulation, analysis |
| Web Search | SerpAPI | Real-time product data from the web |
| Backend | FastAPI | REST API + HTML template serving |
| Frontend | Vanilla JS + Jinja2 | Chat UI with real-time markdown rendering |
| Parallelism | ThreadPoolExecutor | Concurrent agent execution |
| Testing | pytest + unittest.mock | 30/30 tests, zero real API calls |
| Containerization | Docker | Portable deployment |

---

## Project Structure

```
Product-Pilot/
│
├── app/                            # FastAPI application
│   ├── main.py                     # Entry point, UTF-8 setup, lifespan
│   ├── api/
│   │   └── routes.py               # /api/query, /api/health endpoints
│   ├── core/
│   │   ├── workflow.py             # LangGraph StateGraph definition
│   │   ├── http_client.py          # Shared HTTP client
│   │   └── request_context.py      # Per-request context
│   ├── models/
│   │   └── graph_state.py          # Shared state TypedDict
│   ├── static/
│   │   ├── css/style.css           # UI styles + table/list formatting
│   │   └── js/app.js               # Chat UI + custom markdown parser
│   └── templates/
│       └── index.html              # Main chat interface
│
├── nodes/                          # LangGraph agent nodes
│   ├── intent_classifier.py        # Classifies query intent
│   ├── product_extractor.py        # Extracts product names
│   ├── supervisor_agent.py         # Orchestrator: plan + parallel exec
│   ├── product_info_agent.py       # Specs, features, display, camera
│   ├── price_agent.py              # Retail prices + price quality scorer
│   ├── review_agent.py             # User reviews, pros/cons
│   ├── rating_agent.py             # Platform ratings and review counts
│   ├── reflection_node.py          # Quality review before analysis
│   └── analyzer_agent.py           # Final synthesis + recommendation
│
├── tests/
│   └── test_workflow.py            # 30 unit tests (mocked APIs)
│
├── scripts/
│   ├── test_api.py                 # Manual API smoke test
│   └── debug_app.py                # Debug helper
│
├── .github/
│   └── workflows/ci.yml            # GitHub Actions CI pipeline
│
├── Dockerfile                      # Container definition
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- [Google AI Studio API Key](https://aistudio.google.com/) (Gemini)
- [SerpAPI Key](https://serpapi.com/)

### 1. Clone the repository
```bash
git clone https://github.com/rohitaimlpro/Product-Pilot.git
cd Product-Pilot
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
```

Open `.env` and fill in your keys:
```env
GOOGLE_API_KEY=your_google_gemini_api_key
SERPAPI_KEY=your_serpapi_key
```

### 5. Start the server
```bash
uvicorn app.main:app --reload --port 8000
```

Visit **http://localhost:8000** in your browser.

---

## Run with Docker

```bash
# Build the image
docker build -t product-pilot .

# Run with your .env file
docker run -p 8000:8000 --env-file .env product-pilot
```

---

## Run Tests

```bash
pytest tests/ -v
```

All 30 tests use mocked SerpAPI and Gemini responses — **no API keys required** to run the test suite.

```
tests/test_workflow.py::test_has_data_empty_list          PASSED
tests/test_workflow.py::test_has_data_with_prices         PASSED
tests/test_workflow.py::test_reflect_good_product_info    PASSED
tests/test_workflow.py::test_price_quality_high_three     PASSED
tests/test_workflow.py::test_price_agent_uses_hints       PASSED
... (30/30 passing)
```

---

## Example Queries

| Query | Agents Used | Response Time |
|---|---|---|
| `which is more affordable iPhone 14 Pro Max or iPhone 15` | 1 agent | ~15s |
| `compare specs and price of OnePlus 12 vs Pixel 8` | 2 agents | ~15s |
| `which has better reviews and ratings Samsung S24 vs iPhone 15` | 2 agents | ~15s |
| `compare Samsung Galaxy S24 vs iPhone 15` | 4 agents | ~20s |
| `recommend me a gaming laptop under 80000` | 4 agents | ~20s |

---

## API Reference

### `POST /api/query`

Request:
```json
{
  "query": "compare iPhone 15 vs Samsung S24"
}
```

Response:
```json
{
  "recommendation": "## iPhone 15 vs Samsung Galaxy S24\n\n| Feature | iPhone 15 | Samsung S24 |\n...",
  "agents_executed": ["product_info_agent", "price_agent", "review_agent", "rating_agent"],
  "confidence_score": 8
}
```

### `GET /api/health`

```json
{
  "status": "healthy",
  "model": "gemini-2.5-flash"
}
```

---

## How Agents Are Selected

The supervisor sends one LLM call with the user's query and a strict selection prompt. It returns a JSON array of only the agents needed:

```python
# "which is cheaper" → ["price_agent"]
# "compare specs"    → ["product_info_agent"]
# "compare X vs Y"   → ["product_info_agent", "price_agent", "review_agent", "rating_agent"]
```

This means simple price queries run in ~15s instead of waiting for all 4 agents.

---

## Performance Highlights

| Metric | Before | After |
|---|---|---|
| Sequential → Parallel | 60s | 15s (4× faster) |
| Gemini unbounded reasoning | 290s | 64s (thinking_budget cap) |
| Test coverage | 0 tests | 30/30 passing |
| Agents per query (selective) | Always 4 | 1–4 based on intent |

---

## License

MIT — feel free to use, fork, and build on this.

---

<div align="center">
Built with LangGraph · Google Gemini 2.5 Flash · FastAPI · SerpAPI
</div>
