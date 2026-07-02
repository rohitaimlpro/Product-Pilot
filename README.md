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

Type a natural language query like *"which is more affordable iPhone 14 Pro Max or iPhone 15"* or *"compare Samsung S24 vs iPhone 15"* — Product Pilot routes it through a 3-node LangGraph pipeline, fetches real-time data via SerpAPI, and returns a structured comparison with prices, specs, reviews, and ratings.

---

## Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                   USER QUERY (Natural Language)                  ║
╚══════════════════════════╦═══════════════════════════════════════╝
                           │
          ┌────────────────▼─────────────────┐
          │         SUPERVISOR NODE           │
          │         (1 LLM call)              │
          │                                   │
          │  ① Parse: intent + products       │
          │  ② Plan: minimum agents needed    │
          │                                   │
          │  recommendation? → call rec_agent │
          │  comparison?     → products ready │
          │                                   │
          │  ③ PARALLEL EXECUTE               │
          │  ┌──────────┬──────────┐          │
          │  │price_agent│info_agent│ (only   │
          │  ├──────────┼──────────┤  agents  │
          │  │review_ag │rating_ag │  needed) │
          │  └──────────┴──────────┘          │
          │  each: ACT → OBSERVE → RETRY      │
          └────────────────┬─────────────────┘
                           │
          ┌────────────────▼─────────────────┐
          │      REFLECT & SCORE NODE         │
          │         (1 LLM call)              │
          │                                   │
          │  • Scores data confidence (1-10)  │
          │  • Writes quality reflection      │
          │  • score < 7 → fallback agent     │
          └────────────────┬─────────────────┘
                           │
          ┌────────────────▼─────────────────┐
          │         ANALYZER NODE             │
          │         (1 LLM call)              │
          │                                   │
          │  Synthesizes all collected data   │
          │  into final structured response   │
          └────────────────┬─────────────────┘
                           │
          ╔════════════════▼═════════════════╗
          ║      STRUCTURED RECOMMENDATION   ║
          ╚══════════════════════════════════╝
```

**LangGraph graph — 3 nodes, straight line:**
```
supervisor ──► reflect_and_score ──► analyzer ──► END
```

---

## Performance

| Query Type | Agents Run | Response Time | Confidence |
|---|---|---|---|
| `"which is more affordable iPhone 14 Pro Max or iPhone 15"` | 1 | **12s** | 9/10 |
| `"compare specs and price of OnePlus 12 vs Pixel 8"` | 2 | **23s** | 9/10 |
| `"compare Samsung Galaxy S24 vs iPhone 15"` | 4 | **33s** | 10/10 |

**Latency optimization history:**

| Optimization | LLM Calls | Worst-case latency |
|---|---|---|
| Original (sequential agents) | 6 | ~77s |
| Parallel agent execution | 6 | ~60s |
| Merged intent+extractor into supervisor | 5 | ~55s |
| Merged confidence+reflection into one call | 4 | ~50s |
| Supervisor absorbs query parsing | 3 | ~40s |
| Reduced analyzer `thinking_budget` 1024→256 | 3 | **~33s** |

---

## Key Features

### 3 LLM Calls Per Query
The entire pipeline runs on exactly 3 Gemini API calls — down from 6 in the original design. Each merged call was a deliberate decision to eliminate redundant LLM round-trips.

```
Call 1 — Supervisor:        intent + product extraction + agent planning
Call 2 — Reflect & Score:   confidence scoring (1-10) + quality reflection
Call 3 — Analyzer:          final synthesis into structured recommendation
```

### Selective Agent Planning
The supervisor's LLM call selects only the agents the query actually needs:

| Query Intent | Agents Selected |
|---|---|
| `"which is cheaper?"` | `price_agent` only |
| `"compare specs and price"` | `product_info_agent` + `price_agent` |
| `"better reviews and ratings?"` | `review_agent` + `rating_agent` |
| `"compare X vs Y"` (broad) | All 4 agents |

### Parallel Agent Execution
Selected agents run simultaneously via `ThreadPoolExecutor`:
```
Sequential (old): price(15s) + info(15s) + review(15s) + rating(15s) = 60s
Parallel  (now):  all 4 agents at once                               = 15s ✅
```

### ACT → OBSERVE → REFORMULATE → RETRY
Every data agent follows a self-correcting loop:
1. **ACT** — search SerpAPI for product data
2. **OBSERVE** — rule-based quality check (high / medium / low)
3. **REFORMULATE** — LLM generates better search queries on poor results
4. **RETRY** — re-search with improved queries

### Reflect & Score (Merged Node)
Replaces two back-to-back LLM calls with one. Returns confidence score + reflection summary together. If score < 7, triggers a fallback agent automatically before passing to analyzer.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Agent Orchestration | LangGraph (StateGraph) | 3-node graph pipeline |
| LLM | Google Gemini 2.5 Flash | Planning, scoring, analysis |
| Web Search | SerpAPI | Real-time product data |
| Backend | FastAPI | REST API + HTML serving |
| Frontend | Vanilla JS + Jinja2 | Chat UI + markdown rendering |
| Parallelism | ThreadPoolExecutor | Concurrent agent execution |
| Testing | pytest + unittest.mock | 30/30 tests, zero real API calls |
| Containerization | Docker | Portable deployment |

---

## Project Structure

```
Product-Pilot/
│
├── app/
│   ├── main.py                      # Entry point
│   ├── api/routes.py                # /api/query, /api/health
│   ├── core/workflow.py             # LangGraph 3-node graph
│   ├── models/graph_state.py        # Shared state TypedDict
│   ├── static/
│   │   ├── css/style.css            # UI + table styles
│   │   └── js/app.js                # Chat UI + markdown parser
│   └── templates/index.html
│
├── nodes/
│   ├── supervisor_agent.py          # Entry point: parse + plan + parallel exec
│   ├── reflect_and_score.py         # Confidence scoring + reflection (1 LLM call)
│   ├── analyzer_agent.py            # Final synthesis
│   ├── recommendation_agent.py      # Generates products for open-ended queries
│   ├── product_info_agent.py        # Specs, features, display, camera
│   ├── price_agent.py               # Retail prices + quality scorer
│   ├── review_agent.py              # User reviews, pros/cons
│   └── rating_agent.py              # Platform ratings and counts
│
├── tests/
│   └── test_workflow.py             # 30 unit tests (mocked APIs)
│
├── .github/workflows/ci.yml         # GitHub Actions CI
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- [Google AI Studio API Key](https://aistudio.google.com/)
- [SerpAPI Key](https://serpapi.com/)

### 1. Clone
```bash
git clone https://github.com/rohitaimlpro/Product-Pilot.git
cd Product-Pilot
```

### 2. Virtual environment
```bash
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/Mac
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment variables
```bash
cp .env.example .env
```
```env
GOOGLE_API_KEY=your_google_gemini_api_key
SERPAPI_KEY=your_serpapi_key
```

### 5. Run
```bash
uvicorn app.main:app --reload --port 8000
```

Visit **http://localhost:8000**

---

## Docker

```bash
docker build -t product-pilot .
docker run -p 8000:8000 --env-file .env product-pilot
```

---

## Tests

```bash
pytest tests/ -v
```

30 tests, all mocked — no API keys needed.

---

## API

### `POST /api/query`
```json
{ "query": "compare iPhone 15 vs Samsung S24" }
```
```json
{
  "recommendation": "...",
  "agents_executed": ["price_agent", "product_info_agent", "review_agent", "rating_agent"],
  "confidence_score": 10
}
```

### `GET /api/health`
```json
{ "status": "ok" }
```

---

## License

MIT
