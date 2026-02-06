"""
============================================================================
INVENTRA - Database Tools
============================================================================

Tools for agents to query inventory and supplier data.
These are wrapped as LangChain tools for use with tool-calling agents.

AVAILABLE TOOLS:
---------------
- get_inventory_data: Query all inventory items
- get_low_stock_items: Get items below reorder point
- get_inventory_by_category: Filter by product category
- run_custom_query: Execute custom SQL (read-only)

SECURITY:
---------
All tools only allow SELECT queries.
No data modification is possible through these tools.

============================================================================
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from langchain_core.tools import tool

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db import run_query, get_table_schema, init_db


# =============================================================================
# INVENTORY QUERY TOOLS
# =============================================================================

@tool
def get_inventory_data(limit: int = 50) -> str:
    """
    Get all inventory items with their current stock levels.
    
    Returns a summary of all products including:
    - SKU ID and name
    - Category
    - Current stock (units_on_hand)
    - Reorder point
    - Supplier information
    
    Args:
        limit: Maximum number of items to return (default 50)
        
    Returns:
        str: Formatted inventory data or error message
    """
    query = f"""
    SELECT 
        i.sku_id,
        i.sku_name,
        i.category,
        i.units_on_hand,
        i.reorder_point,
        i.units_on_order,
        i.unit_cost,
        i.unit_price,
        i.weather_sensitive,
        s.supplier_name,
        s.lead_time_days
    FROM inventory i
    JOIN suppliers s ON i.supplier_id = s.supplier_id
    ORDER BY i.category, i.sku_name
    LIMIT {limit}
    """
    
    try:
        df = run_query(query)
        if "error" in df.columns:
            return f"Error querying inventory: {df['error'].iloc[0]}"
        
        # Format as readable string
        result = f"Found {len(df)} inventory items:\n\n"
        for _, row in df.iterrows():
            stock_status = "[LOW]" if row['units_on_hand'] <= row['reorder_point'] else "[OK]"
            weather_flag = "[Weather]" if row['weather_sensitive'] else ""
            result += (
                f"• {row['sku_id']}: {row['sku_name']} {weather_flag}\n"
                f"  Category: {row['category']}\n"
                f"  Stock: {row['units_on_hand']} units ({stock_status})\n"
                f"  Reorder Point: {row['reorder_point']}\n"
                f"  Supplier: {row['supplier_name']} ({row['lead_time_days']} days lead time)\n\n"
            )
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_low_stock_items() -> str:
    """
    Get all items that are at or below their reorder point.
    
    These items need immediate attention for restocking.
    Returns detailed information including supplier and lead time.
    
    Returns:
        str: List of low stock items with reorder recommendations
    """
    query = """
    SELECT 
        i.sku_id,
        i.sku_name,
        i.category,
        i.units_on_hand,
        i.reorder_point,
        i.target_stock,
        i.unit_cost,
        i.avg_daily_sales,
        i.weather_sensitive,
        s.supplier_name,
        s.supplier_id,
        s.lead_time_days,
        s.min_order_qty
    FROM inventory i
    JOIN suppliers s ON i.supplier_id = s.supplier_id
    WHERE i.units_on_hand <= i.reorder_point
    ORDER BY (i.units_on_hand - i.reorder_point) ASC
    """
    
    try:
        df = run_query(query)
        if "error" in df.columns:
            return f"Error querying low stock items: {df['error'].iloc[0]}"
        
        if len(df) == 0:
            return "[OK] All inventory items are above their reorder points. No immediate restocking needed."
        
        result = f"[WARNING] Found {len(df)} items below reorder point:\n\n"
        
        for _, row in df.iterrows():
            # Calculate recommended order quantity
            deficit = row['reorder_point'] - row['units_on_hand']
            days_until_stockout = row['units_on_hand'] / max(row['avg_daily_sales'], 0.1)
            recommended_qty = max(row['target_stock'] - row['units_on_hand'], row['min_order_qty'])
            
            result += (
                f"[!] {row['sku_id']}: {row['sku_name']}\n"
                f"   Category: {row['category']}\n"
                f"   Current Stock: {row['units_on_hand']} (Reorder at: {row['reorder_point']})\n"
                f"   Deficit: {deficit} units below threshold\n"
                f"   Days Until Stockout: ~{days_until_stockout:.1f} days\n"
                f"   Avg Daily Sales: {row['avg_daily_sales']:.1f} units\n"
                f"   Supplier: {row['supplier_name']} (Lead Time: {row['lead_time_days']} days)\n"
                f"   Recommended Order: {recommended_qty} units (min: {row['min_order_qty']})\n\n"
            )
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_inventory_by_category(category: str) -> str:
    """
    Get all inventory items for a specific category.
    
    Categories include: Umbrellas, Raincoats, Summer Wear, Winter Wear, 
    Electronics, Home Essentials
    
    Args:
        category: Product category to filter by
        
    Returns:
        str: Inventory items in that category
    """
    query = """
    SELECT 
        i.sku_id,
        i.sku_name,
        i.units_on_hand,
        i.reorder_point,
        i.unit_price,
        i.avg_daily_sales,
        i.sales_last_7d,
        i.sales_last_30d,
        i.weather_sensitive,
        s.supplier_name
    FROM inventory i
    JOIN suppliers s ON i.supplier_id = s.supplier_id
    WHERE LOWER(i.category) LIKE LOWER(?)
    ORDER BY i.sku_name
    """
    
    try:
        # Use wildcard for partial matching
        df = run_query(query, (f"%{category}%",))
        if "error" in df.columns:
            return f"Error: {df['error'].iloc[0]}"
        
        if len(df) == 0:
            return f"No items found in category '{category}'. Available categories: Umbrellas, Raincoats, Summer Wear, Winter Wear, Electronics, Home Essentials"
        
        result = f"[INVENTORY] {len(df)} items in '{category}':\n\n"
        
        total_value = 0
        for _, row in df.iterrows():
            stock_status = "[LOW]" if row['units_on_hand'] <= row['reorder_point'] else "[OK]"
            weather_flag = "[Weather-Sensitive]" if row['weather_sensitive'] else ""
            stock_value = row['units_on_hand'] * row['unit_price']
            total_value += stock_value
            
            result += (
                f"{stock_status} {row['sku_id']}: {row['sku_name']}\n"
                f"   Stock: {row['units_on_hand']} units | Value: ₹{stock_value:,.0f}\n"
                f"   Sales: {row['sales_last_7d']} (7d) / {row['sales_last_30d']} (30d)\n"
                f"   Supplier: {row['supplier_name']} | {weather_flag}\n\n"
            )
        
        result += f"\nTotal Stock Value: Rs.{total_value:,.0f}"
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_weather_sensitive_products() -> str:
    """
    Get all products that are sensitive to weather conditions.
    
    Weather-sensitive products have demand that changes based on:
    - Rain: Umbrellas, Raincoats
    - Heat: Summer Wear
    - Cold: Winter Wear
    
    Returns:
        str: List of weather-sensitive products with demand patterns
    """
    query = """
    SELECT 
        i.sku_id,
        i.sku_name,
        i.category,
        i.units_on_hand,
        i.reorder_point,
        i.avg_daily_sales,
        wp.weather_condition,
        wp.demand_multiplier,
        wp.notes as weather_notes
    FROM inventory i
    LEFT JOIN weather_products wp ON i.category = wp.affected_category
    WHERE i.weather_sensitive = 1
    ORDER BY i.category, i.sku_name
    """
    
    try:
        df = run_query(query)
        if "error" in df.columns:
            return f"Error: {df['error'].iloc[0]}"
        
        result = "[WEATHER] Weather-Sensitive Products:\n\n"
        
        current_category = ""
        for _, row in df.iterrows():
            if row['category'] != current_category:
                current_category = row['category']
                result += f"\n[{current_category}]\n"
                result += "-" * 40 + "\n"
            
            multiplier = row.get('demand_multiplier', 1.0) or 1.0
            condition = row.get('weather_condition', 'normal') or 'normal'
            
            result += (
                f"• {row['sku_name']}: {row['units_on_hand']} units\n"
                f"  {condition.title()} → {multiplier:.1f}x demand\n"
            )
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"
