# 🛍️ PRODUCT PILOT AI — Product Recommendation System

An intelligent product recommendation system powered by LangGraph and Google Gemini AI, now featuring a FastAPI backend with a clean HTML, CSS, and JavaScript frontend, and deployed seamlessly on Render.

## 🌟 Features

- 🧠 **LangGraph-Powered Multi-Agent System** for intent classification, product extraction, and recommendation
- 🤖 **Google Gemini AI Integration** for advanced natural language understanding
- 🔄 **FastAPI Backend** serving REST endpoints and HTML templates
- 🎨 **Interactive Web Frontend** built with HTML, CSS, and JavaScript
- ⚙️ **Real-Time Product Insights** including specifications, pricing, reviews, and comparisons
- ☁️ **Deployed on Render** for global accessibility

## 🏗️ System Architecture

```
User Query → FastAPI → LangGraph Workflow → Multi-Agent Processing → Gemini AI → Response
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11
- Google API Key (Gemini)
- SERP API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/ai-product-recommendation-system.git
   cd ai-product-recommendation-system
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   python -m venv venv
   venv\Scripts\activate      # For Windows
   # source venv/bin/activate  # For Linux/Mac
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   SERP_API_KEY=your_serp_api_key_here
   ```

4. **Run the FastAPI application locally**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Open your browser**
   
   Visit 👉 http://localhost:8000

## 🌐 Deployment on Render

The app is deployed on Render as a web service.

**Start Command (Render):**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

You can view your deployed app at:
🔗 https://product-pilot-2.onrender.com/

## 📦 Project Structure

```
product_recommendation_system/
│
├── app/
│   ├── main.py                     # FastAPI entry point
│   ├── api/
│   │   ├── routes.py               # API route definitions
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py               # Configuration and environment loading
│   │   ├── logger.py               # Logging setup
│   │   ├── mailer.py               # Optional mailing functions
│   │   └── workflow.py             # LangGraph workflow orchestration
│   ├── models/
│   │   ├── graph_state.py          # Graph state definitions
│   │   └── __init__.py
│   ├── static/                     # Frontend static files
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── templates/
│       └── index.html              # Frontend HTML template
│
├── nodes/                          # LangGraph agent nodes
│   ├── analyzer_agent.py
│   ├── intent_classifier.py
│   ├── price_agent.py
│   ├── product_extractor.py
│   ├── product_info_agent.py
│   ├── rating_agent.py
│   ├── recommendation_agent.py
│   ├── review_agent.py
│   └── supervisor_agent.py
│
├── .env                            # Environment variables
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
└── render.yaml (optional)          # Render deployment configuration
```

## 🤖 Core Agents

| Agent | Description |
|-------|-------------|
| **Intent Classifier** | Detects if the user wants recommendations or comparisons |
| **Product Extractor** | Identifies product names or categories |
| **Supervisor Agent** | Coordinates all workflow agents |
| **Recommendation Agent** | Generates AI-driven product suggestions |
| **Product Info Agent** | Fetches specifications and features |
| **Price Agent** | Gathers price details from SERP API |
| **Review Agent** | Analyzes product reviews |
| **Rating Agent** | Collects user ratings |
| **Analyzer Agent** | Combines data into final insights |

## 🧱 Frontend Overview

The frontend uses:
- `index.html` for the main interface
- `style.css` for design
- `app.js` for interactive elements and API calls

**Example JS call to FastAPI endpoint:**
```javascript
fetch("/api/recommend", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ query: "Best phones under ₹30000" })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

## 🧰 Dependencies

```
fastapi
uvicorn[standard]
jinja2
python-dotenv
requests
langchain
langgraph
langchain-google-genai
google-generativeai
typing-extensions
```

## ⚙️ Configuration

### Google Gemini API
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Generate an API key and add it to `.env`

### SERP API
1. Visit [SerpAPI](https://serpapi.com/)
2. Get your API key and add it to `.env`

## 🧪 Example Queries

**Recommendations:**
- "Suggest a good gaming laptop under ₹1 lakh"
- "Recommend a smartwatch for fitness tracking"

**Comparisons:**
- "Compare iPhone 15 vs Samsung Galaxy S24"
- "Which is better: AirPods Pro or Sony WH-1000XM4?"

## 📈 Future Improvements

- [ ] Add authentication for user-specific recommendations
- [ ] Integrate caching for faster response
- [ ] Add analytics dashboard for query trends
- [ ] Implement user feedback system
- [ ] Multi-language support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'Add new feature'`)
4. Push and open a Pull Request

## 📄 License

Licensed under the MIT License — see the [LICENSE](LICENSE) file.

---

Made with ❤️ using **FastAPI**, **LangGraph**, and **Google Gemini AI** — deployed on **Render**.
