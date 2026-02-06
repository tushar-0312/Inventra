# ============================================================================
# INVENTRA - Agents Package
# ============================================================================
# 
# This package contains the multi-agent system components:
#
# Core Components:
# - state.py       : LangGraph GlobalState definition
# - graph.py       : Main graph builder and workflow
#
# Agents:
# - supervisor.py  : Routes queries to appropriate agents
# - data_agent.py  : Retrieves and analyzes inventory data
# - weather_agent.py : Provides weather forecasts and impact analysis
# - decision_agent.py : Makes inventory recommendations
#
# Usage:
#   from agents import build_graph, run_query, GlobalState
# ============================================================================

from .state import GlobalState, create_initial_state
from .graph import build_graph, run_query, get_final_response

__all__ = [
    "GlobalState", 
    "create_initial_state",
    "build_graph", 
    "run_query",
    "get_final_response"
]
