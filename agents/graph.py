"""
============================================================================
INVENTRA - Main LangGraph Workflow
============================================================================

This module builds the complete multi-agent workflow using LangGraph.
It connects all agents (Supervisor, Data, Weather, Decision) into a
cohesive workflow with conditional routing.

WORKFLOW ARCHITECTURE:
---------------------
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
              ┌─────│  SUPERVISOR │─────┐
              │     └──────┬──────┘     │
              │            │            │
       ┌──────▼───┐  ┌─────▼────┐ ┌────▼─────┐
       │   DATA   │  │ WEATHER  │ │ DECISION │
       └──────┬───┘  └────┬─────┘ └────┬─────┘
              │           │            │
              └───────────┴─────┬──────┘
                          ┌─────▼─────┐
                          │    END    │
                          └───────────┘

USAGE:
------
    from agents.graph import build_graph, run_query
    
    # Build the graph
    graph = build_graph()
    
    # Run a query
    response = run_query(graph, "What items are low on stock?")

============================================================================
"""

import os
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

# Local imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.state import GlobalState, create_initial_state, get_last_message_content, get_user_query
from agents.supervisor import supervisor_node, get_next_agent
from agents.data_agent import simple_data_agent_node
from agents.weather_agent import simple_weather_agent_node
from agents.decision_agent import simple_decision_agent_node
from database.db import init_db

# Load environment variables
load_dotenv()


# =============================================================================
# GRAPH CONFIGURATION
# =============================================================================

# Maximum recursion limit (prevents infinite loops)
RECURSION_LIMIT = int(os.getenv("RECURSION_LIMIT", "25"))


# =============================================================================
# NODE DEFINITIONS
# =============================================================================

def start_node(state: GlobalState) -> Dict[str, Any]:
    """
    Entry point node that initializes the workflow.
    
    Analyzes the query and routes to the most relevant agent.
    
    Args:
        state: Initial global state
        
    Returns:
        dict: State with next set to appropriate agent
    """
    print("\n" + "=" * 60)
    print("[START] INVENTRA Multi-Agent System Started")
    print("=" * 60)
    
    # Initialize database
    db_status = init_db()
    if db_status.get("ok"):
        print(f"[DB] Database: {db_status.get('total_rows')} rows in {len(db_status.get('tables', []))} tables")
    else:
        print(f"[WARNING] Database warning: {db_status.get('error')}")
    
    # Smart routing based on query keywords
    query = get_user_query(state).lower()
    
    # Weather-specific queries -> Weather Agent first
    weather_keywords = ["weather", "forecast", "rain", "monsoon", "temperature", "climate", "hot", "cold"]
    if any(kw in query for kw in weather_keywords):
        print("[ROUTER] Query is weather-related -> WEATHER agent")
        return {"next": "WEATHER"}
    
    # Decision/recommendation queries -> Decision Agent (but needs data first)
    decision_keywords = ["recommend", "reorder", "order", "purchase", "ticket", "action", "should i"]
    if any(kw in query for kw in decision_keywords):
        print("[ROUTER] Query needs recommendations -> DATA then DECISION")
        return {"next": "DATA"}
    
    # Default: Inventory/data queries -> Data Agent only
    print("[ROUTER] Query is data-related -> DATA agent")
    return {"next": "DATA"}


def end_node(state: GlobalState) -> Dict[str, Any]:
    """
    Final node that compiles the response.
    
    Args:
        state: Final global state
        
    Returns:
        dict: Final state (no changes)
    """
    print("\n" + "=" * 60)
    print("[COMPLETE] INVENTRA Workflow Complete")
    print("=" * 60)
    
    return {}


# =============================================================================
# ROUTING LOGIC
# =============================================================================

def route_from_data(state: GlobalState) -> str:
    """
    Route from Data Agent to next node.
    
    Based on what was found, route to Weather or Decision.
    """
    next_agent = state.get("next", "END")
    
    # Validate routing
    if next_agent == "WEATHER":
        return "weather"
    elif next_agent == "DECISION":
        return "decision"
    else:
        return "end"


def route_from_weather(state: GlobalState) -> str:
    """
    Route from Weather Agent to next node.
    
    Almost always goes to Decision Agent.
    """
    next_agent = state.get("next", "DECISION")
    
    if next_agent == "DECISION":
        return "decision"
    else:
        return "end"


def route_from_decision(state: GlobalState) -> str:
    """
    Route from Decision Agent to next node.
    
    Usually ends, but could loop back if more analysis needed.
    """
    return "end"


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def build_graph(use_memory: bool = True) -> StateGraph:
    """
    Build the complete LangGraph workflow.
    
    Creates a state graph with all agent nodes and conditional routing.
    
    Args:
        use_memory: Whether to use in-memory checkpointing
        
    Returns:
        StateGraph: Compiled graph ready for execution
        
    Example:
        >>> graph = build_graph()
        >>> result = graph.invoke({"messages": [HumanMessage(content="...")]})
    """
    # Create the state graph with our GlobalState schema
    workflow = StateGraph(GlobalState)
    
    # -------------------------------------------------------------------------
    # ADD NODES
    # -------------------------------------------------------------------------
    
    # Entry and exit nodes
    workflow.add_node("start", start_node)
    workflow.add_node("end", end_node)
    
    # Agent nodes (using simple versions for reliability)
    workflow.add_node("data", simple_data_agent_node)
    workflow.add_node("weather", simple_weather_agent_node)
    workflow.add_node("decision", simple_decision_agent_node)
    
    # -------------------------------------------------------------------------
    # ADD EDGES
    # -------------------------------------------------------------------------
    
    # Set the entry point
    workflow.set_entry_point("start")
    
    # Conditional routing from Start based on query analysis
    def route_from_start(state: GlobalState) -> str:
        """Route from start to the appropriate first agent."""
        next_agent = state.get("next", "DATA")
        if next_agent == "WEATHER":
            return "weather"
        elif next_agent == "DECISION":
            return "decision"
        else:
            return "data"
    
    workflow.add_conditional_edges(
        "start",
        route_from_start,
        {
            "data": "data",
            "weather": "weather",
            "decision": "decision"
        }
    )
    
    # Conditional routing from Data Agent
    workflow.add_conditional_edges(
        "data",
        route_from_data,
        {
            "weather": "weather",
            "decision": "decision",
            "end": "end"
        }
    )
    
    # Conditional routing from Weather Agent
    workflow.add_conditional_edges(
        "weather",
        route_from_weather,
        {
            "decision": "decision",
            "end": "end"
        }
    )
    
    # Decision Agent always goes to end
    workflow.add_edge("decision", "end")
    
    # Set the finish point
    workflow.set_finish_point("end")
    
    # -------------------------------------------------------------------------
    # COMPILE
    # -------------------------------------------------------------------------
    
    if use_memory:
        # Add memory checkpoint for conversation history
        memory = MemorySaver()
        compiled = workflow.compile(checkpointer=memory)
    else:
        compiled = workflow.compile()
    
    print("[OK] Graph compiled successfully")
    
    return compiled


# =============================================================================
# QUERY RUNNER
# =============================================================================

def run_query(
    graph, 
    query: str, 
    thread_id: str = "main",
    region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a user query through the multi-agent workflow.
    
    This is the main entry point for using the Inventra system.
    
    Args:
        graph: Compiled LangGraph workflow
        query: User's natural language query
        thread_id: Conversation thread ID for memory
        region: Optional region for weather queries
        
    Returns:
        dict: Final state with all agent outputs
        
    Example:
        >>> graph = build_graph()
        >>> result = run_query(graph, "What items are low on stock?")
        >>> print(result["messages"][-1].content)
    """
    # Create initial state
    initial_state = create_initial_state(query)
    
    if region:
        initial_state["region"] = region
    
    # Configure the run
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": RECURSION_LIMIT
    }
    
    print(f"\n[QUERY] Query: {query}")
    print("-" * 60)
    
    # Run the graph
    try:
        final_state = graph.invoke(initial_state, config)
        
        # Extract the final response
        messages = final_state.get("messages", [])
        if messages:
            print(f"\n[OUTPUT] Final Response (from last agent):")
            print(messages[-1].content[:500])
        
        return final_state
        
    except Exception as e:
        print(f"[ERROR] Error running query: {str(e)}")
        return {
            "error": str(e),
            "query": query
        }


def get_final_response(state: Dict[str, Any]) -> str:
    """
    Extract the final human-readable response from state.
    
    Compiles all agent outputs into a cohesive response.
    
    Args:
        state: Final workflow state
        
    Returns:
        str: Compiled response for the user
    """
    parts = []
    
    messages = state.get("messages", [])
    
    # Compile messages from each agent
    for msg in messages:
        if hasattr(msg, "content") and msg.content:
            parts.append(msg.content)
    
    # Add recommendations if present
    recommendations = state.get("recommendations", {})
    if recommendations.get("analysis"):
        parts.append(f"\n## Recommendations\n{recommendations['analysis']}")
    
    return "\n\n---\n\n".join(parts)


# =============================================================================
# MAIN / TESTING
# =============================================================================

if __name__ == "__main__":
    print("Building and testing Inventra Graph...")
    print("=" * 60)
    
    # Build the graph
    graph = build_graph(use_memory=False)
    
    # Test queries
    test_queries = [
        "What items are low on stock?",
        # "How will weather affect umbrella sales in Mumbai?",
        # "Generate reorder recommendations"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: {query}")
        print("=" * 60)
        
        result = run_query(graph, query)
        
        if result.get("error"):
            print(f"Error: {result['error']}")
        else:
            response = get_final_response(result)
            print(f"\n[RESPONSE] Full Response:\n{response[:1000]}...")
        
        print("\n" + "=" * 60)
