
from typing import Dict, Any
import streamlit as st
import time

# Import the individual agent functions
from nodes.product_info_agent import product_info_agent_node
from nodes.price_agent import price_agent_node
from nodes.review_agent import review_rating_agent_node
from nodes.rating_agent import rating_platform_agent_node

def log_message(step, message, data=None):
    """Helper to log both to console and Streamlit debug logger"""
    print(f"{step}: {message}")
    if data:
        print(f"  Data: {data}")
    
    # Also log to Streamlit debug logger if available
    if hasattr(st.session_state, 'debug_logger'):
        st.session_state.debug_logger.log(step, message, data)

def has_data(data):
    """Check if data actually contains meaningful information"""
    if not data:
        return False
    
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                # Check if any of the data fields have content
                if 'prices' in item and item['prices']:
                    return True
                if 'reviews' in item:
                    reviews = item['reviews']
                    if isinstance(reviews, dict):
                        if reviews.get('positive_reviews') or reviews.get('negative_reviews'):
                            return True
                if 'info' in item and item['info']:
                    return True
                if 'ratings' in item and item['ratings']:
                    return True
        return False
    
    return False

def supervisor_agent_node(state: dict) -> dict:
    """
    Supervisor agent that coordinates data collection - SEQUENTIAL for free tier
    """
    try:
        log_message("SUPERVISOR_START", "Supervisor agent started", {
            "products_count": len(state.get("products", []))
        })
        
        products = state.get("products", [])
        price_data = state.get("price_data", [])
        review_data = state.get("review_data", [])
        product_info = state.get("product_info", [])
        platform_rating_data = state.get("platform_rating_data", [])
        
        data_status = {
            "products": products,
            "has_price_data": has_data(price_data),
            "has_review_data": has_data(review_data),
            "has_product_info": has_data(product_info),
            "has_rating_data": has_data(platform_rating_data)
        }
        
        log_message("SUPERVISOR_STATUS", "Current data status", data_status)
        
        # If no products identified, can't proceed
        if not products:
            log_message("SUPERVISOR_SKIP", "No products found - skipping data collection")
            return {
                **state,
                "missing_data": [],
                "current_step": "No products to analyze - skipping data collection"
            }
        
        # Identify missing data
        missing_data = []
        agents_to_run = []
        
        if not has_data(product_info):
            missing_data.append("product_info")
            agents_to_run.append(("product_info_agent", product_info_agent_node))
        
        if not has_data(price_data):
            missing_data.append("price_data")
            agents_to_run.append(("price_agent", price_agent_node))
            
        if not has_data(review_data):
            missing_data.append("review_data")
            agents_to_run.append(("review_agent", review_rating_agent_node))
            
        if not has_data(platform_rating_data):
            missing_data.append("rating_data")
            agents_to_run.append(("rating_agent", rating_platform_agent_node))
        
        log_message("SUPERVISOR_MISSING", f"Missing data types: {missing_data}", {
            "missing_count": len(missing_data),
            "agents_to_run": [name for name, _ in agents_to_run]
        })
        
        # If no missing data, we're done
        if not missing_data:
            log_message("SUPERVISOR_COMPLETE", "All data already collected")
            return {
                **state,
                "missing_data": [],
                "current_step": "All data collected - ready for analysis"
            }
        
        log_message("SUPERVISOR_SEQUENTIAL", f"Running {len(agents_to_run)} agents SEQUENTIALLY (free tier rate limit compliance)")
        
        # Run agents SEQUENTIALLY to respect free tier rate limits
        updated_state = state.copy()
        errors = []
        completed = 0
        
        for agent_name, agent_func in agents_to_run:
            try:
                log_message("AGENT_START", f"Running {agent_name}")
                
                # Run the agent
                result_state = agent_func(updated_state)
                
                # Merge the specific data from agent result
                if agent_name == "product_info_agent" and "product_info" in result_state:
                    updated_state["product_info"] = result_state["product_info"]
                    log_message("SUPERVISOR_MERGE", f"Merged product_info", {
                        "items": len(result_state['product_info'])
                    })
                    
                elif agent_name == "price_agent" and "price_data" in result_state:
                    updated_state["price_data"] = result_state["price_data"]
                    log_message("SUPERVISOR_MERGE", f"Merged price_data", {
                        "items": len(result_state['price_data'])
                    })
                    
                elif agent_name == "review_agent" and "review_data" in result_state:
                    updated_state["review_data"] = result_state["review_data"]
                    log_message("SUPERVISOR_MERGE", f"Merged review_data", {
                        "items": len(result_state['review_data'])
                    })
                    
                elif agent_name == "rating_agent" and "platform_rating_data" in result_state:
                    updated_state["platform_rating_data"] = result_state["platform_rating_data"]
                    log_message("SUPERVISOR_MERGE", f"Merged platform_rating_data", {
                        "items": len(result_state['platform_rating_data'])
                    })
                
                completed += 1
                log_message("AGENT_COMPLETE", f"{agent_name} completed successfully")
                
                # Small delay between agents to be extra safe with rate limits
                if agent_name != agents_to_run[-1][0]:  # Don't delay after last agent
                    time.sleep(0.5)
                
            except Exception as e:
                error_msg = f"{agent_name}: {str(e)}"
                errors.append(error_msg)
                log_message("AGENT_ERROR", error_msg)
        
        # Update step status
        step_message = f"Sequential execution complete - {completed}/{len(agents_to_run)} agents successful"
        
        if errors:
            step_message += f". Errors: {'; '.join(errors)}"
        
        log_message("SUPERVISOR_DONE", step_message, {
            "completed": completed,
            "total": len(agents_to_run),
            "errors": errors
        })
        
        return {
            **updated_state,
            "missing_data": [],
            "current_step": step_message
        }
        
    except Exception as e:
        log_message("SUPERVISOR_ERROR", f"Supervisor error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            **state,
            "missing_data": [],
            "current_step": f"Supervisor error: {str(e)}"
        }