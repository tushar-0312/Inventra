# ============================================================================
# INVENTRA - Tools Package
# ============================================================================
# 
# This package provides tools that agents can use to interact with
# external systems (database, weather, ticketing).
#
# Tools:
# - db_tools.py      : Database query tools
# - weather_tools.py : Mock weather data tools
# - ticket_tools.py  : Mock ticket generation tools
#
# Usage:
#   from tools import get_inventory_data, get_weather_forecast, create_ticket
# ============================================================================

from .db_tools import get_inventory_data, get_low_stock_items, get_inventory_by_category
from .weather_tools import get_weather_forecast, get_weather_impact
from .ticket_tools import create_reorder_ticket, create_alert_ticket

__all__ = [
    "get_inventory_data",
    "get_low_stock_items", 
    "get_inventory_by_category",
    "get_weather_forecast",
    "get_weather_impact",
    "create_reorder_ticket",
    "create_alert_ticket"
]
