"""
============================================================================
INVENTRA - LangGraph Global State Definition
============================================================================

This module defines the shared state structure for the multi-agent system.
All agents read from and write to this state as they process queries.

STATE ARCHITECTURE:
------------------
The state follows a "blackboard" pattern where:
1. User query enters the system
2. Each agent reads relevant context and adds its output
3. Final response is compiled from accumulated state

KEY STATE FIELDS:
----------------
- messages: Conversation history (LangChain message format)
- next: Router decision for next agent (DATA/WEATHER/DECISION/END)
- inventory_context: Data retrieved by Data Agent
- weather_context: Weather analysis from Weather Agent
- recommendations: Final decisions from Decision Agent

USAGE:
------
    from agents.state import GlobalState
    
    # Initialize state
    state: GlobalState = {
        "messages": [HumanMessage(content="...")],
        "next": "DATA"
    }

============================================================================
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator

from langchain_core.messages import BaseMessage


# =============================================================================
# GLOBAL STATE DEFINITION
# =============================================================================

class GlobalState(TypedDict, total=False):
    """
    Shared state for the Inventra multi-agent workflow.
    
    This TypedDict defines all fields that can be passed between agents.
    Using `total=False` makes all fields optional with defaults.
    
    Attributes:
        messages: List of conversation messages (accumulates via operator.add)
        next: Routing decision - which agent to invoke next
        
        inventory_context: Data context from Data Agent
        weather_context: Weather analysis from Weather Agent
        recommendations: Final recommendations from Decision Agent
        tickets: Generated tickets for actions (mock MCP)
        
        error: Error message if any agent fails
    """
    
    # -------------------------------------------------------------------------
    # CORE MESSAGING
    # -------------------------------------------------------------------------
    # Message history - uses operator.add to accumulate messages from all agents
    # Annotated with operator.add so LangGraph knows to append, not replace
    messages: Annotated[List[BaseMessage], operator.add]
    
    # -------------------------------------------------------------------------
    # ROUTING
    # -------------------------------------------------------------------------
    # Next agent to invoke: "DATA", "WEATHER", "DECISION", "END"
    # Set by the Supervisor based on query analysis
    next: str
    
    # Reason for routing decision (for debugging/explainability)
    routing_reason: str
    
    # -------------------------------------------------------------------------
    # AGENT OUTPUTS
    # -------------------------------------------------------------------------
    # Context from Data Agent - inventory analysis, low stock items, etc.
    inventory_context: Dict[str, Any]
    
    # Context from Weather Agent - forecasts, risk levels, demand multipliers
    weather_context: Dict[str, Any]
    
    # Final recommendations from Decision Agent
    recommendations: Dict[str, Any]
    
    # Generated tickets (mock MCP output)
    tickets: List[Dict[str, Any]]
    
    # -------------------------------------------------------------------------
    # METADATA
    # -------------------------------------------------------------------------
    # Error message if any step fails
    error: Optional[str]
    
    # Query classification (inventory_query, weather_query, forecast_query, etc.)
    query_type: str
    
    # Region specified in query (for weather lookups)
    region: str


# =============================================================================
# STATE INITIALIZATION HELPERS
# =============================================================================

def create_initial_state(user_message: str) -> GlobalState:
    """
    Create a fresh state for a new user query.
    
    This is the entry point for each user interaction.
    
    Args:
        user_message: The user's query text
        
    Returns:
        GlobalState: Initialized state ready for processing
        
    Example:
        >>> state = create_initial_state("What items are low on stock?")
        >>> # Now pass state to the graph
    """
    from langchain_core.messages import HumanMessage
    
    return {
        "messages": [HumanMessage(content=user_message)],
        "next": "DATA",  # Always start with Data Agent
        "inventory_context": {},
        "weather_context": {},
        "recommendations": {},
        "tickets": [],
        "error": None,
        "routing_reason": "",
        "query_type": "",
        "region": ""
    }


def get_last_message_content(state: GlobalState) -> str:
    """
    Get the content of the last message in state.
    
    Useful for agents to see the most recent output.
    
    Args:
        state: Current global state
        
    Returns:
        str: Content of the last message, or empty string if none
    """
    messages = state.get("messages", [])
    if messages:
        return messages[-1].content or ""
    return ""


def get_user_query(state: GlobalState) -> str:
    """
    Extract the original user query from state.
    
    Searches through messages to find the first HumanMessage.
    
    Args:
        state: Current global state
        
    Returns:
        str: The user's original query
    """
    from langchain_core.messages import HumanMessage
    
    messages = state.get("messages", [])
    for msg in messages:
        if isinstance(msg, HumanMessage):
            return msg.content or ""
    return ""
