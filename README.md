# Multi-Agent AI Product Recommendation System

An intelligent product research assistant built with **LangGraph** that uses multiple specialized AI agents to compare products, fetch prices, analyze reviews, and deliver structured recommendations — powered by **Google Gemini 2.5 Flash** and **SerpAPI**.

---

## Architecture

```
User Query
    │
    ▼
Intent Classifier        ← classifies query type
    │
    ▼
Product Extractor        ← extracts product names from query
    │
    ▼
Supervisor Agent         ← PLAN: selects minimum agents needed
    │                       EXECUTE: runs agents in parallel
    ├──► Price Agent          → current retail prices
    ├──► Product Info Agent   → specs, features, display, camera
    ├──► Review Agent         → user reviews, pros/cons
    └──► Rating Agent         → platform ratings & counts
    │
    ▼
Reflection Node          ← reviews data quality
    │
    ▼
Analyzer Agent           ← synthesizes all data into final answer
    │
    ▼
Structured Recommendation
```

---

## Key Features

### Selective LLM Planning
The supervisor reads the user's query and selects only the agents needed — not all four every time.
- `"which is more affordable?"` → runs only `price_agent`
- `"compare specs and price"` → runs `product_info_agent` + `price_agent`
- `"compare X vs Y"` (broad) → runs all 4 agents

### Parallel Agent Execution
All planned agents run simultaneously via `ThreadPoolExecutor`, reducing wall-clock latency **4× (60s → 15s)** compared to sequential execution.

### ACT → OBSERVE → REFORMULATE → RETRY
Each agent follows an agentic loop:
1. **ACT** — search for product data via SerpAPI
2. **OBSERVE** — rule-based quality check (high / medium / low confidence)
3. **REFORMULATE** — LLM generates better search queries on poor results
4. **RETRY** — re-run the search with improved queries

### Confidence Scoring
After all agents finish, an LLM scores data sufficiency (1–10). If score < 7, a fallback agent is triggered automatically.

### Optimized Gemini Reasoning
`thinking_budget` caps (1024 for analyzer, 512 for reflection) prevent unbounded reasoning, cutting total response time from **290s → 64s**.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph (StateGraph) |
| LLM | Google Gemini 2.5 Flash |
| Web Search | SerpAPI |
| Backend | FastAPI |
| Frontend | Vanilla JS + Jinja2 |
| Testing | pytest (30/30 tests, mocked APIs) |
| Containerization | Docker |

---

## Project Structure

```
├── app/
│   ├── api/routes.py           # FastAPI endpoints
│   ├── core/workflow.py        # LangGraph graph definition
│   ├── models/graph_state.py   # Shared state schema
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/app.js           # Markdown parser + chat UI
│   └── templates/index.html
├── nodes/
│   ├── intent_classifier.py
│   ├── product_extractor.py
│   ├── supervisor_agent.py     # Parallel orchestration + planning
│   ├── product_info_agent.py
│   ├── price_agent.py
│   ├── review_agent.py
│   ├── rating_agent.py
│   ├── reflection_node.py
│   └── analyzer_agent.py
├── tests/
│   └── test_workflow.py        # 30 unit tests (no real API calls)
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/rohitaimlpro/Product-Pilot.git
cd Product-Pilot
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` and add your keys:
```
GOOGLE_API_KEY=your_google_api_key
SERPAPI_KEY=your_serpapi_key
```

### 5. Run the server
```bash
uvicorn app.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Run with Docker

```bash
docker build -t product-pilot .
docker run -p 8000:8000 --env-file .env product-pilot
```

---

## Run Tests

```bash
pytest tests/ -v
```

All 30 tests mock external APIs (SerpAPI + Gemini) — no API keys needed to run tests.

---

## Example Queries

- `which is more affordable iPhone 14 Pro Max or iPhone 15`
- `compare specs and price of OnePlus 12 vs Pixel 8`
- `which has better reviews Samsung Galaxy S24 or iPhone 15`
- `recommend me a gaming laptop under 80000`
- `compare Samsung Galaxy S24 vs iPhone 15`

---

## API Reference

### `POST /api/query`
```json
{
  "query": "compare iPhone 15 vs Samsung S24"
}
```
**Response:**
```json
{
  "recommendation": "...",
  "agents_executed": ["price_agent", "product_info_agent", "review_agent", "rating_agent"],
  "confidence_score": 8
}
```

### `GET /api/health`
Returns server health status.

---

## License

MIT
