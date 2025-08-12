# 🛍️PRODUCT PILOT AI - Product Recommendation System

An intelligent product recommendation system powered by **LangGraph** and **Google Gemini AI** that provides comprehensive product analysis, price comparisons, reviews, and personalized recommendations.

## 🌟 Features

- **Intelligent Intent Classification**: Automatically determines whether users want recommendations or product comparisons
- **Multi-Agent Architecture**: Specialized agents for different data collection tasks
- **Real-time Data Collection**: Fetches live pricing, reviews, specifications, and ratings
- **Comprehensive Analysis**: AI-powered analysis combining all collected data
- **Interactive Streamlit Interface**: User-friendly web interface with chat functionality
- **API Integration**: Seamless integration with Google Gemini and SERP APIs

## 🏗️ System Architecture
![alt text](<Untitled diagram _ Mermaid Chart-2025-08-12-082556.png>)



## 🚀 Quick Start

### Prerequisites

- Python 3.11
- Google API Key (for Gemini)
- SERP API Key (for web search)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/ai-product-recommendation-system.git
   cd ai-product-recommendation-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   SERP_API_KEY=your_serp_api_key_here
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:8501` to access the application.

## 📦 Dependencies

```txt
streamlit>=1.28.0
langchain>=0.1.0
langchain-openai>=0.1.0
langchain-core>=0.1.0
langgraph>=0.0.30
python-dotenv>=1.0.0
requests>=2.31.0
typing-extensions>=4.5.0
langchain-google-genai>=1.0.0 
google-generativeai>=0.3.0     
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
python-multipart==0.0.6
```

## 🔧 Configuration

### API Keys Setup

#### Google Gemini API
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file or enter it in the Streamlit sidebar

#### SERP API
1. Visit [SerpAPI](https://serpapi.com/)
2. Sign up and get your API key
3. Add it to your `.env` file or enter it in the Streamlit sidebar

## 🎯 Usage Examples

### Product Recommendations
```
"Recommend a good smartphone under $500"
"I need a laptop for programming"
"Find the best wireless earbuds for workouts"
```

### Product Comparisons
```
"Compare iPhone 15 vs Samsung Galaxy S24"
"MacBook Air vs Dell XPS 13 comparison"
"Which is better: AirPods Pro or Sony WH-1000XM4?"
```

## 🏗️ Project Structure

```
ai-product-recommendation-system/
│
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables
├── README.md                      # Project documentation
│
└── nodes/                         # LangGraph node modules
    ├── __init__.py
    ├── intent_classifier.py       # Intent classification logic
    ├── product_extractor.py       # Product name extraction
    ├── recommendation_agent.py    # Product recommendation generation
    ├── supervisor_agent.py        # Central coordination logic
    ├── product_info_agent.py      # Product information collection
    ├── price_agent.py             # Price data collection
    ├── review_agent.py            # Review analysis
    ├── rating_agent.py            # Rating collection
    └── analyzer_agent.py          # Final analysis and recommendations
```

## 🤖 System Components

### Core Agents

1. **Intent Classifier** 🎯
   - Determines user intent (recommendation vs comparison)
   - Routes queries to appropriate processing paths

2. **Recommendation Agent** 🏆
   - Generates product suggestions based on user requirements
   - Uses AI to understand context and preferences

3. **Product Extractor** 🔍
   - Extracts specific product names from comparison queries
   - Handles various product naming formats

4. **Supervisor Agent** 👑
   - Coordinates all data collection activities
   - Manages workflow state and missing data detection

5. **Data Collection Agents**
   - **Price Agent** 💰: Collects pricing information from multiple sources
   - **Review Agent** ⭐: Analyzes user reviews and sentiment
   - **Product Info Agent** 📋: Gathers specifications and features
   - **Rating Agent** 📈: Collects platform ratings and scores

6. **Analyzer Agent** 🧠
   - Synthesizes all collected data
   - Generates comprehensive recommendations

### External Integrations

- **Google Gemini LLM**: Powers natural language understanding and generation
- **SERP API**: Enables real-time web search for product data

## 🎨 User Interface

The Streamlit interface provides:
- **Chat Interface**: Interactive conversation with the AI system
- **Settings Panel**: Easy API key configuration
- **Workflow Status**: Real-time processing updates
- **Chat History**: Persistent conversation history
- **Example Queries**: Quick-start examples for users

## 🔄 Workflow Process

1. **User Query Input**: User submits a product-related question
2. **Intent Analysis**: AI classifies the query type
3. **Product Processing**: Generate recommendations or extract product names
4. **Supervisor Coordination**: Central agent manages data collection
5. **Parallel Data Collection**: Multiple agents gather different data types
6. **Data Synthesis**: All information is combined and analyzed
7. **Final Recommendation**: Comprehensive response delivered to user

## 🛠️ Development

### Adding New Agents

1. Create a new file in the `nodes/` directory
2. Implement the agent function following the existing pattern:
   ```python
   def your_agent_node(state: dict) -> dict:
       # Your agent logic here
       return {
           **state,
           "your_data": result,
           "current_step": "Your step description"
       }
   ```
3. Import and add the agent to the workflow in `app.py`

### Customization

- **Modify prompts**: Update AI prompts in individual agent files
- **Add data sources**: Integrate additional APIs in agent implementations
- **Enhance UI**: Customize the Streamlit interface in `app.py`
- **Extend state**: Add new fields to the `GraphState` TypedDict

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure API keys are correctly set in `.env` or Streamlit sidebar
   - Verify API key permissions and quotas

2. **Import Errors**
   - Check that all dependencies are installed
   - Verify Python version compatibility

3. **Network Issues**
   - Check internet connection for API calls
   - Verify firewall settings allow outbound HTTPS requests

### Debug Mode

Enable debug logging by adding to your `.env`:
```env
STREAMLIT_LOGGER_LEVEL=debug
```

## 📈 Performance Optimization

- **Caching**: Uses Streamlit's `@st.cache_resource` for LLM initialization
- **Parallel Processing**: Multiple agents can work simultaneously
- **Rate Limiting**: Built-in delays to respect API rate limits
- **Error Handling**: Comprehensive error handling and fallbacks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) for the excellent framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) for multi-agent orchestration
- [Google Gemini](https://deepmind.google/technologies/gemini/) for powerful AI capabilities
- [Streamlit](https://streamlit.io/) for the beautiful web interface
- [SERP API](https://serpapi.com/) for reliable web search functionality

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review existing discussions

---

**Made with ❤️ using LangGraph and Google Gemini AI** 
