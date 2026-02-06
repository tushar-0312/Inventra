"""
============================================================================
INVENTRA - Mock Ticket Tools
============================================================================

Mock MCP-based ticketing tools for the Decision Agent.
These tools simulate ticket generation for inventory actions.

In Phase 2, these can be connected to real systems like:
- Jira
- Notion
- Slack
- Email notifications

AVAILABLE TOOLS:
---------------
- create_reorder_ticket: Create a purchase order ticket
- create_alert_ticket: Create an alert for anomalies
- get_pending_tickets: List all pending tickets

============================================================================
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from langchain_core.tools import tool


# =============================================================================
# IN-MEMORY TICKET STORAGE (Mock)
# =============================================================================

# Store tickets in memory (would be database in production)
_TICKETS: List[Dict[str, Any]] = []


# =============================================================================
# TICKET CREATION TOOLS
# =============================================================================

@tool
def create_reorder_ticket(
    sku_id: str,
    sku_name: str,
    quantity: int,
    supplier_name: str,
    reason: str,
    priority: str = "medium"
) -> str:
    """
    Create a purchase reorder ticket for an inventory item.
    
    This generates a mock ticket that would normally be sent to
    a procurement system like Jira or Notion.
    
    Args:
        sku_id: Product SKU identifier
        sku_name: Product name
        quantity: Quantity to order
        supplier_name: Supplier to order from
        reason: Reason for the reorder (e.g., "low stock", "weather demand")
        priority: Priority level (low, medium, high, urgent)
        
    Returns:
        str: Ticket confirmation with ID
    """
    # Generate ticket
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    
    ticket = {
        "ticket_id": ticket_id,
        "type": "REORDER",
        "status": "PENDING",
        "priority": priority.upper(),
        "created_at": datetime.now().isoformat(),
        "data": {
            "sku_id": sku_id,
            "sku_name": sku_name,
            "quantity": quantity,
            "supplier_name": supplier_name,
            "reason": reason
        }
    }
    
    _TICKETS.append(ticket)
    
    # Format response
    priority_emoji = {
        "low": "[LOW]",
        "medium": "[MED]",
        "high": "[HIGH]",
        "urgent": "[URGENT]"
    }.get(priority.lower(), "[MED]")
    
    result = f"""
[SUCCESS] REORDER TICKET CREATED
================================
{priority_emoji} Ticket ID: {ticket_id}
Priority: {priority.upper()}
Status: PENDING

Product: {sku_name} ({sku_id})
Quantity: {quantity} units
Supplier: {supplier_name}
Reason: {reason}

Created: {datetime.now().strftime("%Y-%m-%d %H:%M")}

[This is a mock ticket - would be sent to Jira/Notion in production]
"""
    
    return result


@tool
def create_alert_ticket(
    category: str,
    alert_type: str,
    severity: str,
    description: str,
    recommended_action: str
) -> str:
    """
    Create an alert ticket for inventory or weather anomalies.
    
    Used for situations like:
    - Stockout warnings
    - Unusual demand patterns
    - Weather-related demand spikes
    - Budget impact alerts
    
    Args:
        category: Product category or "SYSTEM"
        alert_type: Type of alert (STOCKOUT_WARNING, DEMAND_SPIKE, WEATHER_ALERT, etc.)
        severity: Severity level (info, warning, critical)
        description: Description of the alert
        recommended_action: What action should be taken
        
    Returns:
        str: Alert confirmation with ID
    """
    ticket_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
    
    ticket = {
        "ticket_id": ticket_id,
        "type": "ALERT",
        "status": "OPEN",
        "severity": severity.upper(),
        "created_at": datetime.now().isoformat(),
        "data": {
            "category": category,
            "alert_type": alert_type,
            "description": description,
            "recommended_action": recommended_action
        }
    }
    
    _TICKETS.append(ticket)
    
    # Format response
    severity_emoji = {
        "info": "[INFO]",
        "warning": "[WARNING]",
        "critical": "[CRITICAL]"
    }.get(severity.lower(), "[WARNING]")
    
    result = f"""
{severity_emoji} ALERT TICKET CREATED
===========================
Ticket ID: {ticket_id}
Type: {alert_type}
Severity: {severity.upper()}
Status: OPEN

Category: {category}
Description: {description}

Recommended Action:
   {recommended_action}

Created: {datetime.now().strftime("%Y-%m-%d %H:%M")}

[This is a mock alert - would trigger notifications in production]
"""
    
    return result


@tool
def get_pending_tickets() -> str:
    """
    Get all pending and open tickets.
    
    Returns a summary of all tickets that need action.
    
    Returns:
        str: List of pending tickets
    """
    pending = [t for t in _TICKETS if t["status"] in ("PENDING", "OPEN")]
    
    if not pending:
        return "[OK] No pending tickets. All inventory actions are up to date."
    
    result = f"PENDING TICKETS ({len(pending)} total)\n"
    result += "=" * 50 + "\n\n"
    
    # Group by type
    reorders = [t for t in pending if t["type"] == "REORDER"]
    alerts = [t for t in pending if t["type"] == "ALERT"]
    
    if reorders:
        result += "REORDER TICKETS:\n"
        result += "-" * 30 + "\n"
        for t in reorders:
            data = t["data"]
            result += (
                f"• {t['ticket_id']} [{t['priority']}]\n"
                f"  {data['sku_name']}: {data['quantity']} units\n"
                f"  Supplier: {data['supplier_name']}\n\n"
            )
    
    if alerts:
        result += "ALERT TICKETS:\n"
        result += "-" * 30 + "\n"
        for t in alerts:
            data = t["data"]
            result += (
                f"• {t['ticket_id']} [{t['severity']}]\n"
                f"  Type: {data['alert_type']}\n"
                f"  {data['description'][:50]}...\n\n"
            )
    
    return result


def get_all_tickets() -> List[Dict[str, Any]]:
    """
    Get all tickets (for debugging/testing).
    
    Returns:
        list: All ticket records
    """
    return _TICKETS.copy()


def clear_tickets() -> None:
    """
    Clear all tickets (for testing).
    """
    _TICKETS.clear()
