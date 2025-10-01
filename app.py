import streamlit as st
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
import json
import traceback
from datetime import datetime

# Import all node modules
from nodes.intent_classifier import intent_classifier_node
from nodes.product_extractor import extract_product_names_node
from nodes.recommendation_agent import recommendation_agent_node
from nodes.supervisor_agent import supervisor_agent_node
from nodes.product_info_agent import product_info_agent_node
from nodes.price_agent import price_agent_node
from nodes.review_agent import review_rating_agent_node
from nodes.rating_agent import rating_platform_agent_node
from nodes.analyzer_agent import analyzer_agent_node

# Load environment variables
load_dotenv()

# Debug logger
class DebugLogger:
    def __init__(self):
        self.logs = []
    
    def log(self, step, message, data=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "step": step,
            "message": message,
            "data": data
        }
        self.logs.append(log_entry)
        print(f"[{timestamp}] {step}: {message}")
        if data:
            print(f"  Data: {data}")
    
    def clear(self):
        self.logs = []
    
    def get_logs(self):
        return self.logs

# Initialize LLM
@st.cache_resource
def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Google API Key not found! Please add it in the sidebar.")
        return None
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.1,
            google_api_key=api_key
        )
        print("✅ LLM initialized successfully")
        return llm
    except Exception as e:
        st.error(f"Failed to initialize LLM: {str(e)}")
        return None

# State definition for LangGraph
class GraphState(TypedDict):
    input: str
    intent: str
    products: List[str]
    price_data: List[Dict]
    review_data: List[Dict]
    product_info: List[Dict]
    platform_rating_data: List[Dict]
    final_recommendation: str
    current_step: str
    missing_data: List[str]

def create_workflow():
    """Create and return the LangGraph workflow with parallel execution support"""
    
    # Initialize the graph
    workflow = StateGraph(GraphState)
    
    # Add all nodes
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("extract_products", extract_product_names_node)
    workflow.add_node("recommendation_agent", recommendation_agent_node)
    workflow.add_node("supervisor", supervisor_agent_node)
    workflow.add_node("analyzer", analyzer_agent_node)
    
    # Set entry point
    workflow.set_entry_point("intent_classifier")
    
    # Define conditional routing from intent classifier
    def route_intent(state: GraphState) -> str:
        intent = state.get("intent", "")
        logger = st.session_state.get('debug_logger')
        if logger:
            logger.log("ROUTING", f"Intent detected: '{intent}'", {"intent": intent})
        
        if "recommendation" in intent.lower():
            if logger:
                logger.log("ROUTING", "Routing to recommendation_agent")
            return "recommendation_agent"
        elif "comparison" in intent.lower():
            if logger:
                logger.log("ROUTING", "Routing to extract_products")
            return "extract_products"
        else:
            if logger:
                logger.log("ROUTING", "Default routing to recommendation_agent")
            return "recommendation_agent"
    
    # Simplified supervisor routing
    def supervisor_routing(state: GraphState) -> str:
        logger = st.session_state.get('debug_logger')
        if logger:
            logger.log("SUPERVISOR_ROUTING", "Moving to analyzer", {
                "products": state.get("products"),
                "has_price_data": len(state.get("price_data", [])) > 0,
                "has_review_data": len(state.get("review_data", [])) > 0,
                "has_product_info": len(state.get("product_info", [])) > 0
            })
        return "analyzer"
    
    # Add edges
    workflow.add_conditional_edges(
        "intent_classifier",
        route_intent,
        {
            "recommendation_agent": "recommendation_agent",
            "extract_products": "extract_products"
        }
    )
    
    workflow.add_edge("recommendation_agent", "supervisor")
    workflow.add_edge("extract_products", "supervisor")
    
    workflow.add_conditional_edges(
        "supervisor",
        supervisor_routing,
        {
            "analyzer": "analyzer"
        }
    )
    
    workflow.add_edge("analyzer", END)
    
    return workflow.compile()

def main():
    st.set_page_config(
        page_title="ProductPilot Debug",
        page_icon="🛍️",
        layout="wide"
    )
    
    st.title("🛍️ ProductPilot - Debug Mode")
    st.markdown("Get intelligent product recommendations with full workflow visibility!")
    
    # Initialize debug logger
    if 'debug_logger' not in st.session_state:
        st.session_state.debug_logger = DebugLogger()
    
    # Initialize session state
    if 'workflow' not in st.session_state:
        try:
            st.session_state.workflow = create_workflow()
            st.session_state.debug_logger.log("INIT", "Workflow created successfully")
        except Exception as e:
            st.error(f"Failed to create workflow: {str(e)}")
            st.session_state.debug_logger.log("INIT", f"Workflow creation failed: {str(e)}")
            st.session_state.workflow = None
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API Key input
        google_key = st.text_input(
            "Google API Key (Gemini)",
            type="password",
            value=os.getenv("GOOGLE_API_KEY", ""),
            help="Enter your Google API key for Gemini"
        )
        
        serp_key = st.text_input(
            "SERP API Key", 
            type="password",
            value=os.getenv("SERP_API_KEY", ""),
            help="Enter your SERP API key for web search"
        )
        
        if st.button("Update Keys"):
            os.environ["GOOGLE_API_KEY"] = google_key
            os.environ["SERP_API_KEY"] = serp_key
            if hasattr(st.session_state, 'workflow'):
                del st.session_state.workflow
            st.success("Keys updated!")
            st.rerun()
        
        st.markdown("---")
        
        # Debug toggle
        show_debug = st.checkbox("Show Debug Panel", value=True)
        
        st.markdown("---")
        st.markdown("### 📝 Example Queries")
        st.markdown("""
        - "Recommend a good smartphone under $500"
        - "Compare iPhone 15 vs Samsung Galaxy S24"
        - "I need a laptop for programming"
        - "Find the best wireless earbuds"
        """)
        
        st.markdown("---")
        st.markdown("### 🔍 API Status")
        st.write(f"Google API: {'✅' if os.getenv('GOOGLE_API_KEY') else '❌'}")
        st.write(f"SERP API: {'✅' if os.getenv('SERP_API_KEY') else '❌'}")
    
    # Check API keys
    if not os.getenv("GOOGLE_API_KEY"):
        st.warning("⚠️ Please enter your Google API Key in the sidebar to get started!")
        return
    
    if not os.getenv("SERP_API_KEY"):
        st.info("ℹ️ SERP API Key not set. Web search functionality will be limited.")
    
    # Main layout
    if show_debug:
        col1, col2 = st.columns([1.5, 1])
    else:
        col1 = st.container()
        col2 = None
    
    with col1:
        st.header("💬 Chat Interface")
        
        # Chat history display
        if st.session_state.chat_history:
            for i, (query, response, status) in enumerate(st.session_state.chat_history):
                with st.expander(f"Query {i+1}: {query[:50]}...", expanded=(i == len(st.session_state.chat_history)-1)):
                    st.markdown(f"**You:** {query}")
                    if status == "success":
                        st.markdown(f"**Assistant:** {response}")
                    else:
                        st.error(f"**Error:** {response}")
        
        # Input form
        with st.form("query_form", clear_on_submit=True):
            user_input = st.text_area(
                "What product are you looking for?",
                placeholder="e.g., I need a good laptop for gaming under $1000",
                height=100
            )
            
            col_a, col_b = st.columns([3, 1])
            with col_a:
                submitted = st.form_submit_button("🔍 Get Recommendation", use_container_width=True)
            with col_b:
                clear_debug = st.form_submit_button("🗑️ Clear Debug", use_container_width=True)
        
        if clear_debug:
            st.session_state.debug_logger.clear()
            st.rerun()
        
        if submitted and user_input.strip():
            if not st.session_state.workflow:
                st.error("Workflow not initialized. Please check your API keys.")
                return
            
            # Clear previous debug logs
            st.session_state.debug_logger.clear()
            st.session_state.debug_logger.log("START", "New query received", {"query": user_input})
            
            with st.spinner("🤖 Processing your request..."):
                try:
                    # Initialize state
                    initial_state = GraphState(
                        input=user_input.strip(),
                        intent="",
                        products=[],
                        price_data=[],
                        review_data=[],
                        product_info=[],
                        platform_rating_data=[],
                        final_recommendation="",
                        current_step="",
                        missing_data=[]
                    )
                    
                    st.session_state.debug_logger.log("STATE_INIT", "Initial state created", initial_state)
                    
                    # Run the workflow
                    st.session_state.debug_logger.log("WORKFLOW", "Starting workflow execution")
                    result = st.session_state.workflow.invoke(initial_state)
                    st.session_state.debug_logger.log("WORKFLOW", "Workflow completed", result)
                    
                    # Display result
                    recommendation = result.get("final_recommendation", "Sorry, I couldn't generate a recommendation.")
                    
                    st.session_state.debug_logger.log("RESULT", "Final recommendation generated", {
                        "recommendation_length": len(recommendation),
                        "has_products": len(result.get("products", [])) > 0
                    })
                    
                    # Add to chat history with success status
                    st.session_state.chat_history.append((user_input, recommendation, "success"))
                    
                    # Force rerun to display new chat
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"An error occurred: {str(e)}"
                    error_trace = traceback.format_exc()
                    st.error(error_msg)
                    st.session_state.debug_logger.log("ERROR", error_msg, {"traceback": error_trace})
                    # Add error to chat history
                    st.session_state.chat_history.append((user_input, error_msg, "error"))
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Debug panel
    if show_debug and col2:
        with col2:
            st.header("🔍 Debug Panel")
            
            # Debug logs
            logs = st.session_state.debug_logger.get_logs()
            
            if logs:
                st.subheader("Execution Log")
                
                for log in logs:
                    with st.expander(f"[{log['timestamp']}] {log['step']}", expanded=False):
                        st.write(f"**Message:** {log['message']}")
                        if log['data']:
                            st.json(log['data'])
                
                # Summary stats
                st.markdown("---")
                st.subheader("Summary")
                st.write(f"Total Steps: {len(logs)}")
                
                # Check for common issues
                steps = [log['step'] for log in logs]
                st.write(f"Steps executed: {' → '.join(set(steps))}")
                
                # Check for products
                product_logs = [log for log in logs if 'products' in str(log.get('data', {}))]
                if product_logs:
                    last_product_log = product_logs[-1]
                    products = last_product_log.get('data', {}).get('products', [])
                    st.write(f"Products found: {len(products) if isinstance(products, list) else 'N/A'}")
                
                # Download debug log
                if st.button("📥 Download Debug Log"):
                    debug_json = json.dumps(logs, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=debug_json,
                        file_name=f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            else:
                st.info("No debug logs yet. Submit a query to see the workflow execution.")

if __name__ == "__main__":
    main()