
import streamlit as st
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
import json

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

# Initialize LLM
@st.cache_resource
def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Google API Key not found! Please add it in the sidebar.")
        return None
    
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.1,
        google_api_key=api_key
    )

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

# Updated sections for app.py - Replace the existing workflow creation and routing logic

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
    
    # Note: We don't add individual agent nodes since supervisor handles them internally
    # This simplifies the graph and enables parallel execution
    
    # Set entry point
    workflow.set_entry_point("intent_classifier")
    
    # Define conditional routing from intent classifier
    def route_intent(state: GraphState) -> str:
        intent = state.get("intent", "")
        if "recommendation" in intent.lower():
            return "recommendation_agent"
        elif "comparison" in intent.lower():
            return "extract_products"
        else:
            return "recommendation_agent"  # default
    
    # Simplified supervisor routing - always goes to analyzer after supervisor
    def supervisor_routing(state: GraphState) -> str:
        # Since supervisor now handles all data collection internally,
        # it always proceeds to analyzer
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
    
    # Simplified routing - supervisor always goes to analyzer
    workflow.add_conditional_edges(
        "supervisor",
        supervisor_routing,
        {
            "analyzer": "analyzer"
        }
    )
    
    # End at analyzer
    workflow.add_edge("analyzer", END)
    
    return workflow.compile()
def main():
    st.set_page_config(
        page_title="ProductPilot",
        page_icon="🛍️",
        layout="wide"
    )
    
    st.title("🛍️ ProductPilot")
    st.markdown("Get intelligent product recommendations and comparisons powered by LangGraph!")
    
    # Initialize session state
    if 'workflow' not in st.session_state:
        try:
            st.session_state.workflow = create_workflow()
        except Exception as e:
            st.error(f"Failed to create workflow: {str(e)}")
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
            # Clear cached LLM to use new keys
            if hasattr(st.session_state, 'workflow'):
                del st.session_state.workflow
            st.success("Keys updated!")
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📝 Example Queries")
        st.markdown("""
        - "Recommend a good smartphone under $500"
        - "Compare iPhone 15 vs Samsung Galaxy S24"
        - "I need a laptop for programming"
        - "Find the best wireless earbuds"
        """)
    
    # Check API keys
    if not os.getenv("GOOGLE_API_KEY"):
        st.warning("⚠️ Please enter your Google API Key in the sidebar to get started!")
        return
    
    if not os.getenv("SERP_API_KEY"):
        st.warning("⚠️ Please enter your SERP API Key in the sidebar for web search functionality!")
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
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
            
            submitted = st.form_submit_button("🔍 Get Recommendation", use_container_width=True)
        
        if submitted and user_input.strip():
            if not st.session_state.workflow:
                st.error("Workflow not initialized. Please check your API keys.")
                return
                
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
                    
                    # Run the workflow
                    result = st.session_state.workflow.invoke(initial_state)
                    
                    # Display result
                    recommendation = result.get("final_recommendation", "Sorry, I couldn't generate a recommendation.")
                    
                    # Add to chat history with success status
                    st.session_state.chat_history.append((user_input, recommendation, "success"))
                    
                    # Force rerun to display new chat
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"An error occurred: {str(e)}"
                    st.error(error_msg)
                    # Add error to chat history
                    st.session_state.chat_history.append((user_input, error_msg, "error"))
                    st.error("Please check your API keys and try again.")
    
    
        
        
        
        
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.chat_history = []
            st.rerun()

if __name__ == "__main__":
    main()