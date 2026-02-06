"""
============================================================================
INVENTRA - Supervisor Agent
============================================================================

The Supervisor is the central router of the multi-agent system.
It analyzes user queries and routes them to the appropriate agent.

ARCHITECTURE:
------------
The Supervisor uses a simple JSON-based routing approach:
1. Analyzes the user query
2. Returns a JSON object with {"next": "AGENT_NAME", "reason": "..."}
3. The graph uses this to determine the next node

ROUTING OPTIONS:
---------------
- "DATA": Route to Data Understanding Agent
- "WEATHER": Route to Weather Forecasting Agent
- "DECISION": Route to Decision & Optimization Agent
- "END": Complete the workflow

============================================================================
"""

import os
import json
import re
from typing import Dict, Any, Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

# Local imports - uses relative path since we're in agents package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompts import load_prompt
from agents.state import GlobalState, get_user_query

# Load environment variables
load_dotenv()


# =============================================================================
# CONFIGURATION
# =============================================================================

# Default model for supervisor
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

# Valid routing options
VALID_ROUTES = ["DATA", "WEATHER", "DECISION", "END"]


# =============================================================================
# SUPERVISOR AGENT
# =============================================================================

def create_supervisor() -> ChatGoogleGenerativeAI:
    """
    Create the Supervisor LLM instance.
    
    Uses Gemini with low temperature for consistent routing decisions.
    
    Returns:
        ChatGoogleGenerativeAI: Configured LLM for routing
    """
    return ChatGoogleGenerativeAI(
        model=DEFAULT_MODEL,
        temperature=0,  # Low temperature for deterministic routing
        convert_system_message_to_human=True  # Gemini compatibility
    )


def parse_routing_response(response: str) -> Dict[str, str]:
    """
    Parse the supervisor's JSON routing response.
    
    Handles common edge cases like markdown code blocks or extra text.
    
    Args:
        response: Raw LLM response string
        
    Returns:
        dict: Parsed routing decision {"next": "...", "reason": "..."}
    """
    # Try to extract JSON from the response
    text = response.strip()
    
    # Remove markdown code blocks if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    # Try to find JSON object using regex
    json_match = re.search(r'\{[^}]+\}', text)
    if json_match:
        text = json_match.group()
    
    try:
        result = json.loads(text)
        
        # Validate the response
        if "next" not in result:
            result["next"] = "DATA"  # Default to DATA agent
        
        # Normalize the routing target
        result["next"] = result["next"].upper()
        if result["next"] not in VALID_ROUTES:
            result["next"] = "DATA"
        
        if "reason" not in result:
            result["reason"] = "No reason provided"
            
        return result
        
    except json.JSONDecodeError:
        # If parsing fails, try to extract just the route
        text_upper = text.upper()
        if "END" in text_upper:
            return {"next": "END", "reason": "Parsed from text"}
        elif "WEATHER" in text_upper:
            return {"next": "WEATHER", "reason": "Parsed from text"}
        elif "DECISION" in text_upper:
            return {"next": "DECISION", "reason": "Parsed from text"}
        else:
            return {"next": "DATA", "reason": "Default fallback"}


def build_context_summary(state: GlobalState) -> str:
    """
    Build a summary of current state for the supervisor's context.
    
    This helps the supervisor understand what has already been done
    and what information is available.
    
    Args:
        state: Current global state
        
    Returns:
        str: Formatted context string
    """
    parts = []
    
    # User query
    user_query = get_user_query(state)
    if user_query:
        parts.append(f"User Query: {user_query}")
    
    # Previous agent outputs
    if state.get("inventory_context"):
        parts.append("Inventory Data: Available (from Data Agent)")
    
    if state.get("weather_context"):
        parts.append("Weather Data: Available (from Weather Agent)")
    
    if state.get("recommendations"):
        parts.append("Recommendations: Generated (from Decision Agent)")
    
    if state.get("tickets"):
        num_tickets = len(state["tickets"])
        parts.append(f"Tickets Created: {num_tickets}")
    
    # Message history summary
    messages = state.get("messages", [])
    if len(messages) > 1:
        parts.append(f"Conversation Messages: {len(messages)}")
    
    return "\n".join(parts) if parts else "No context available yet."


def supervisor_node(state: GlobalState) -> Dict[str, Any]:
    """
    Supervisor node for the LangGraph workflow.
    
    This function is called by LangGraph to determine the next agent.
    It analyzes the current state and returns routing instructions.
    
    Args:
        state: Current global state from the graph
        
    Returns:
        dict: Updated state with routing decision
    """
    print("[SUPERVISOR] Analyzing query and determining next agent...")
    
    # Get the user query
    user_query = get_user_query(state)
    
    # Build context for the supervisor
    context = build_context_summary(state)
    
    # Load the supervisor prompt and format it
    prompt_template = load_prompt("supervisor")
    system_prompt = prompt_template.replace("{context}", context)
    
    # Create the supervisor LLM
    llm = create_supervisor()
    
    # Prepare messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User query: {user_query}\n\nDetermine which agent should handle this next.")
    ]
    
    try:
        # Get routing decision
        response = llm.invoke(messages)
        response_text = response.content
        
        # Parse the response
        routing = parse_routing_response(response_text)
        
        print(f"[SUPERVISOR] Routing to: {routing['next']}")
        print(f"   Reason: {routing['reason']}")
        
        # Return updated state
        return {
            "next": routing["next"],
            "routing_reason": routing["reason"]
        }
        
    except Exception as e:
        print(f"[ERROR] [SUPERVISOR] Error: {str(e)}")
        # Default to DATA agent on error
        return {
            "next": "DATA",
            "routing_reason": f"Error occurred, defaulting to DATA: {str(e)}",
            "error": str(e)
        }


def get_next_agent(state: GlobalState) -> Literal["DATA", "WEATHER", "DECISION", "END"]:
    """
    Conditional edge function for LangGraph routing.
    
    This is used as the condition function in add_conditional_edges().
    
    Args:
        state: Current global state
        
    Returns:
        str: Name of the next node to route to
    """
    return state.get("next", "END")


# =============================================================================
# TESTING / DEBUG
# =============================================================================

if __name__ == "__main__":
    # Test the supervisor with a sample query
    from agents.state import create_initial_state
    
    print("Testing Supervisor Agent...")
    print("=" * 50)
    
    test_queries = [
        "What items are low on stock?",
        "How will the weather affect umbrella sales in Mumbai?",
        "Generate reorder recommendations for next week",
        "Thanks, that's all I needed"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        state = create_initial_state(query)
        result = supervisor_node(state)
        print(f"Route: {result.get('next')}, Reason: {result.get('routing_reason')}")
