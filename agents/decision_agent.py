"""
============================================================================
INVENTRA - Decision & Optimization Agent
============================================================================

The Decision Agent synthesizes data from other agents and makes
actionable inventory recommendations with ticket generation.

RESPONSIBILITIES:
----------------
1. Combine inventory + weather data
2. Calculate priority scores for items
3. Determine reorder quantities
4. Generate purchase order tickets
5. Create alerts for stockout risks

TOOLS USED:
----------
- create_reorder_ticket: Generate purchase orders
- create_alert_ticket: Create inventory alerts
- get_pending_tickets: View existing tickets

============================================================================
"""

import os
import re
from typing import Dict, Any, List

from langchain_core.messages import AIMessage
from dotenv import load_dotenv

# Local imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.state import GlobalState, get_user_query
from tools.ticket_tools import (
    create_reorder_ticket,
    create_alert_ticket,
    get_pending_tickets
)

# Load environment variables
load_dotenv()


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")


# =============================================================================
# DECISION AGENT NODE
# =============================================================================

def simple_decision_agent_node(state: GlobalState) -> Dict[str, Any]:
    """
    Decision Agent that analyzes context and generates tickets.
    
    Uses direct tool invocation for reliable operation.
    
    Args:
        state: Current global state
        
    Returns:
        dict: Updated state with recommendations
    """
    print("\n[DECISION AGENT] Generating recommendations...")
    
    user_query = get_user_query(state)
    
    # Get context
    inventory_context = state.get("inventory_context", {})
    weather_context = state.get("weather_context", {})
    
    inv_analysis = inventory_context.get("analysis", "")
    weather_analysis = weather_context.get("analysis", "")
    
    # Check if we have low stock items that need tickets
    has_low_stock = inventory_context.get("has_low_stock", False)
    has_high_weather_impact = weather_context.get("high_impact", False)
    
    tickets_created = []
    output_parts = []
    
    try:
        # Parse low stock items from inventory analysis
        if has_low_stock and inv_analysis:
            # Look for SKU patterns in the analysis
            sku_matches = re.findall(r'([A-Z]+_\d+):\s*([^\n]+)', inv_analysis)
            
            for sku_id, sku_name in sku_matches[:5]:  # Limit to 5 tickets
                # Determine priority based on weather impact
                if has_high_weather_impact and any(cat in inv_analysis.lower() for cat in ["umbrella", "raincoat", "summer", "winter"]):
                    priority = "high"
                    reason = f"Low stock + weather-driven demand expected"
                else:
                    priority = "medium"
                    reason = "Below reorder point"
                
                # Create reorder ticket
                ticket_result = create_reorder_ticket.invoke({
                    "sku_id": sku_id,
                    "sku_name": sku_name.split('\n')[0].strip()[:50],
                    "quantity": 100,  # Default quantity
                    "supplier_name": "Default Supplier",
                    "reason": reason,
                    "priority": priority
                })
                tickets_created.append(ticket_result)
        
        # Create weather alert if needed
        if has_high_weather_impact:
            region = weather_context.get("region", "unknown")
            
            if weather_context.get("has_rain"):
                alert = create_alert_ticket.invoke({
                    "category": "Umbrellas, Raincoats",
                    "alert_type": "WEATHER_DEMAND_SPIKE",
                    "severity": "warning",
                    "description": f"Rain expected in {region} - demand for rain gear may spike 2-3x",
                    "recommended_action": "Increase stock of umbrellas and raincoats"
                })
                tickets_created.append(alert)
            
            if weather_context.get("has_heat"):
                alert = create_alert_ticket.invoke({
                    "category": "Summer Wear",
                    "alert_type": "WEATHER_DEMAND_SPIKE",
                    "severity": "info",
                    "description": f"Hot weather expected in {region} - summer wear demand increasing",
                    "recommended_action": "Monitor summer wear inventory"
                })
                tickets_created.append(alert)
        
        # Build output
        output_parts.append("## Recommendations Summary\n")
        
        if tickets_created:
            output_parts.append(f"Created {len(tickets_created)} tickets:\n")
            for i, ticket in enumerate(tickets_created, 1):
                output_parts.append(f"{i}. {ticket[:200]}...\n")
        else:
            output_parts.append("No immediate actions required. Inventory levels are healthy.\n")
        
        # Add context-based advice
        output_parts.append("\n## Analysis\n")
        if has_low_stock:
            output_parts.append("- Some items are below reorder point - tickets created\n")
        if has_high_weather_impact:
            output_parts.append("- Weather impact detected - consider adjusting stock levels\n")
        if not has_low_stock and not has_high_weather_impact:
            output_parts.append("- All systems normal. Continue regular monitoring.\n")
        
        output = "\n".join(output_parts)
        
        print(f"[DECISION AGENT] Complete. Tickets created: {len(tickets_created)}")
        
        return {
            "messages": [AIMessage(content=f"[Decision Agent]\n{output}")],
            "recommendations": {
                "analysis": output,
                "tickets_created": len(tickets_created)
            },
            "tickets": tickets_created,
            "next": "END"
        }
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"[ERROR] [DECISION AGENT] {error_msg}")
        return {
            "messages": [AIMessage(content=f"[Decision Agent] {error_msg}")],
            "recommendations": {"error": error_msg},
            "next": "END",
            "error": error_msg
        }


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    from agents.state import create_initial_state
    
    print("Testing Decision Agent...")
    print("=" * 50)
    
    # Create state with mock context
    state = create_initial_state("Generate reorder recommendations")
    state["inventory_context"] = {
        "analysis": "UMB_001: Classic Umbrella - LOW STOCK (45 units, reorder at 100)",
        "has_low_stock": True,
        "has_weather_items": True
    }
    state["weather_context"] = {
        "analysis": "Rain expected next 3 days, HIGH DEMAND for umbrellas",
        "region": "mumbai",
        "has_rain": True,
        "high_impact": True
    }
    
    result = simple_decision_agent_node(state)
    
    print("\nResult:")
    print(result["messages"][0].content)
    print(f"\nTickets Created: {len(result.get('tickets', []))}")
