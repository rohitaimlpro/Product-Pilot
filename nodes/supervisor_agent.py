# nodes/supervisor_agent.py - FIXED
# def supervisor_agent_node(state: dict) -> dict:
#     """
#     Supervisor agent that determines what data is missing and coordinates other agents
#     """
#     try:
#         products = state.get("products", [])
#         price_data = state.get("price_data", [])
#         review_data = state.get("review_data", [])
#         product_info = state.get("product_info", [])
#         platform_rating_data = state.get("platform_rating_data", [])
        
#         missing_data = []
        
#         # Check what data is missing for the products we have
#         if products:  # Only check if we have products
#             if not product_info:
#                 missing_data.append("product_info")
#             elif not price_data:
#                 missing_data.append("price_data")
#             elif not review_data:
#                 missing_data.append("review_data")
#             elif not platform_rating_data:
#                 missing_data.append("rating_data")
        
#         return {
#             **state,
#             "missing_data": missing_data,
#             "current_step": f"Supervisor check - Missing: {missing_data}"
#         }
#     except Exception as e:
#         return {
#             **state,
#             "missing_data": [],
#             "current_step": f"Supervisor error: {str(e)}"
#         }
# nodes/supervisor_agent.py - FIXED WITH PARALLEL EXECUTION
import asyncio
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import the individual agent functions
from nodes.product_info_agent import product_info_agent_node
from nodes.price_agent import price_agent_node
from nodes.review_agent import review_rating_agent_node
from nodes.rating_agent import rating_platform_agent_node

def run_agent_parallel(agent_func, state: dict, agent_name: str):
    """Helper function to run an agent and return the result with agent name"""
    try:
        result = agent_func(state)
        return agent_name, result, None
    except Exception as e:
        return agent_name, state, str(e)

def supervisor_agent_node(state: dict) -> dict:
    """
    Enhanced supervisor agent that coordinates data collection and can run agents in parallel
    """
    try:
        products = state.get("products", [])
        price_data = state.get("price_data", [])
        review_data = state.get("review_data", [])
        product_info = state.get("product_info", [])
        platform_rating_data = state.get("platform_rating_data", [])
        
        # If no products identified, can't proceed with data collection
        if not products:
            return {
                **state,
                "missing_data": [],
                "current_step": "No products to analyze - skipping data collection"
            }
        
        missing_data = []
        agents_to_run = []
        
        # Identify what data is missing and which agents need to run
        if not product_info:
            missing_data.append("product_info")
            agents_to_run.append(("product_info_agent", product_info_agent_node))
        
        if not price_data:
            missing_data.append("price_data")
            agents_to_run.append(("price_agent", price_agent_node))
            
        if not review_data:
            missing_data.append("review_data")
            agents_to_run.append(("review_agent", review_rating_agent_node))
            
        if not platform_rating_data:
            missing_data.append("rating_data")
            agents_to_run.append(("rating_agent", rating_platform_agent_node))
        
        # If no missing data, we're done
        if not missing_data:
            return {
                **state,
                "missing_data": [],
                "current_step": "All data collected - ready for analysis"
            }
        
        # Run agents in parallel if multiple agents need to execute
        if len(agents_to_run) > 1:
            updated_state = state.copy()
            errors = []
            
            # Use ThreadPoolExecutor for parallel execution
            with ThreadPoolExecutor(max_workers=min(4, len(agents_to_run))) as executor:
                # Submit all agent tasks
                future_to_agent = {
                    executor.submit(run_agent_parallel, agent_func, state, agent_name): agent_name 
                    for agent_name, agent_func in agents_to_run
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_agent):
                    agent_name, result_state, error = future.result()
                    
                    if error:
                        errors.append(f"{agent_name}: {error}")
                        continue
                    
                    # Merge the specific data from each agent result
                    if agent_name == "product_info_agent" and "product_info" in result_state:
                        updated_state["product_info"] = result_state["product_info"]
                    elif agent_name == "price_agent" and "price_data" in result_state:
                        updated_state["price_data"] = result_state["price_data"]
                    elif agent_name == "review_agent" and "review_data" in result_state:
                        updated_state["review_data"] = result_state["review_data"]
                    elif agent_name == "rating_agent" and "platform_rating_data" in result_state:
                        updated_state["platform_rating_data"] = result_state["platform_rating_data"]
            
            # Update step status
            completed_agents = len(agents_to_run) - len(errors)
            step_message = f"Parallel execution complete - {completed_agents}/{len(agents_to_run)} agents successful"
            
            if errors:
                step_message += f". Errors: {'; '.join(errors)}"
            
            return {
                **updated_state,
                "missing_data": [],  # Clear missing data as we've attempted to collect all
                "current_step": step_message
            }
        
        # If only one agent needs to run, execute it normally
        elif len(agents_to_run) == 1:
            agent_name, agent_func = agents_to_run[0]
            try:
                result_state = agent_func(state)
                return {
                    **result_state,
                    "missing_data": [],
                    "current_step": f"Single agent {agent_name} completed"
                }
            except Exception as e:
                return {
                    **state,
                    "missing_data": [],
                    "current_step": f"Single agent {agent_name} failed: {str(e)}"
                }
        
        # Fallback - should not reach here
        return {
            **state,
            "missing_data": [],
            "current_step": "No agents to run"
        }
        
    except Exception as e:
        return {
            **state,
            "missing_data": [],
            "current_step": f"Supervisor error: {str(e)}"
        }