"""
============================================================================
INVENTRA - Data Understanding Agent
============================================================================

The Data Agent is responsible for querying and analyzing inventory data.
It retrieves stock levels, identifies low stock items, and provides insights.

RESPONSIBILITIES:
----------------
1. Query current inventory levels
2. Identify items below reorder point
3. Analyze sales trends
4. Identify weather-sensitive products
5. Provide data context for other agents

TOOLS USED:
----------
- get_inventory_data: Query all inventory
- get_low_stock_items: Find critical items
- get_inventory_by_category: Filter by category
- get_weather_sensitive_products: Weather-affected items

============================================================================
"""

import os
from typing import Dict, Any, List

from langchain_core.messages import AIMessage
from dotenv import load_dotenv

# Local imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.state import GlobalState, get_user_query
from tools.db_tools import (
    get_inventory_data, 
    get_low_stock_items, 
    get_inventory_by_category,
    get_weather_sensitive_products
)
from database.db import init_db

# Load environment variables
load_dotenv()


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")


# =============================================================================
# DATA AGENT NODE
# =============================================================================

def simple_data_agent_node(state: GlobalState) -> Dict[str, Any]:
    """
    Data Agent that directly calls tools to query inventory.
    
    Uses direct tool invocation for reliable operation.
    
    Args:
        state: Current global state
        
    Returns:
        dict: Updated state with inventory context
    """
    print("\n[DATA AGENT] Querying inventory...")
    
    # Initialize database
    init_db()
    
    user_query = get_user_query(state).lower()
    
    try:
        # Determine which tools to call based on query
        results = []
        
        # Always get low stock items (most common need)
        low_stock = get_low_stock_items.invoke({})
        results.append(("Low Stock Items", low_stock))
        
        # Check for category-specific queries
        categories = ["umbrella", "raincoat", "summer", "winter", "electronic", "home"]
        for cat in categories:
            if cat in user_query:
                cat_data = get_inventory_by_category.invoke({"category": cat})
                results.append((f"{cat.title()} Inventory", cat_data))
                break
        
        # Check for weather-related query
        if "weather" in user_query or "rain" in user_query or "monsoon" in user_query:
            weather_items = get_weather_sensitive_products.invoke({})
            results.append(("Weather-Sensitive Products", weather_items))
        
        # Compile results
        output_parts = []
        for title, data in results:
            output_parts.append(f"## {title}\n{data}")
        
        output = "\n\n".join(output_parts)
        
        # Build context
        inventory_context = {
            "analysis": output,
            "query": user_query,
            "has_low_stock": "low" in output.lower() or "below" in output.lower() or "LOW" in output,
            "has_weather_items": "weather" in output.lower() or "sensitive" in output.lower()
        }
        
        # Suggest next agent only if query explicitly needs more processing
        # For simple data queries, end here
        query_needs_recommendations = any(kw in user_query for kw in ["recommend", "reorder", "order", "action"])
        query_asks_weather = any(kw in user_query for kw in ["weather", "forecast", "rain"])
        
        if query_asks_weather and inventory_context["has_weather_items"]:
            next_agent = "WEATHER"
        elif query_needs_recommendations and inventory_context["has_low_stock"]:
            next_agent = "DECISION"
        else:
            # Simple data query - just end here
            next_agent = "END"
        
        print(f"[DATA AGENT] Complete. Suggesting next: {next_agent}")
        
        return {
            "messages": [AIMessage(content=f"[Data Agent]\n{output}")],
            "inventory_context": inventory_context,
            "next": next_agent
        }
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"[ERROR] [DATA AGENT] {error_msg}")
        return {
            "messages": [AIMessage(content=f"[Data Agent] {error_msg}")],
            "inventory_context": {"error": error_msg},
            "next": "END",
            "error": error_msg
        }


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    from agents.state import create_initial_state
    
    print("Testing Data Agent...")
    print("=" * 50)
    
    # Test with simple query
    state = create_initial_state("What items are low on stock?")
    result = simple_data_agent_node(state)
    
    print("\nResult:")
    print(result["messages"][0].content[:500] + "...")
    print(f"\nNext Agent: {result.get('next')}")
