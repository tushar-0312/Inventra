"""
============================================================================
INVENTRA - Weather Forecasting Agent
============================================================================

The Weather Agent provides weather forecasts and analyzes how weather
conditions will affect inventory demand.

RESPONSIBILITIES:
----------------
1. Get weather forecasts for specified regions
2. Calculate demand impact per product category
3. Identify weather-driven risks and opportunities
4. Provide context for the Decision Agent

TOOLS USED:
----------
- get_weather_forecast: Multi-day forecast for a region
- get_weather_impact: Demand multipliers by category

============================================================================
"""

import os
from typing import Dict, Any

from langchain_core.messages import AIMessage
from dotenv import load_dotenv

# Local imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.state import GlobalState, get_user_query
from tools.weather_tools import get_weather_forecast, get_weather_impact

# Load environment variables
load_dotenv()


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
DEFAULT_REGION = "mumbai"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_region_from_query(query: str) -> str:
    """
    Extract region/city name from user query.
    
    Args:
        query: User query string
        
    Returns:
        str: Detected region or default
    """
    query_lower = query.lower()
    
    # Check for known cities
    cities = ["mumbai", "delhi", "bengaluru", "bangalore", "chennai", "kolkata", "hyderabad"]
    for city in cities:
        if city in query_lower:
            return "bengaluru" if city == "bangalore" else city
    
    return DEFAULT_REGION


# =============================================================================
# WEATHER AGENT NODE
# =============================================================================

def simple_weather_agent_node(state: GlobalState) -> Dict[str, Any]:
    """
    Weather Agent that directly calls weather tools.
    
    Args:
        state: Current global state
        
    Returns:
        dict: Updated state with weather context
    """
    print("\n[WEATHER AGENT] Getting weather data...")
    
    user_query = get_user_query(state)
    region = state.get("region") or extract_region_from_query(user_query)
    
    try:
        # Get forecast
        forecast = get_weather_forecast.invoke({"region": region, "days": 7})
        
        # Get impact analysis
        impact = get_weather_impact.invoke({"region": region, "days": 7})
        
        # Combine results
        output = f"{forecast}\n\n{impact}"
        
        # Build context
        weather_context = {
            "analysis": output,
            "region": region,
            "has_rain": "rain" in output.lower(),
            "has_heat": "hot" in output.lower() or "heat" in output.lower(),
            "has_cold": "cold" in output.lower(),
            "high_impact": "HIGH DEMAND" in output or "2." in output
        }
        
        print(f"[WEATHER AGENT] Complete. Region: {region}")
        
        # Only go to Decision if the query explicitly asks for recommendations
        original_query = user_query.lower()  # user_query already defined above
        needs_decision = any(kw in original_query for kw in ["recommend", "reorder", "order", "action", "what should"])
        
        return {
            "messages": [AIMessage(content=f"[Weather Agent]\n{output}")],
            "weather_context": weather_context,
            "region": region,
            "next": "DECISION" if needs_decision else "END"
        }
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"[ERROR] [WEATHER AGENT] {error_msg}")
        return {
            "messages": [AIMessage(content=f"[Weather Agent] {error_msg}")],
            "weather_context": {"error": error_msg},
            "next": "DECISION",
            "error": error_msg
        }


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    from agents.state import create_initial_state
    
    print("Testing Weather Agent...")
    print("=" * 50)
    
    state = create_initial_state("How will weather affect umbrella sales in Mumbai?")
    result = simple_weather_agent_node(state)
    
    print("\nResult:")
    print(result["messages"][0].content[:800] + "...")
    print(f"\nRegion: {result.get('region')}")
    print(f"Next Agent: {result.get('next')}")
