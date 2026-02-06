"""
============================================================================
INVENTRA - Mock Weather Tools
============================================================================

Mock weather data and forecasting tools for the Weather Agent.
These tools simulate weather API responses for development.

In Phase 2, these will be replaced with real OpenWeatherMap API calls.

AVAILABLE TOOLS:
---------------
- get_weather_forecast: Get weather forecast for a region
- get_weather_impact: Calculate impact on inventory demand

MOCK DATA INCLUDES:
------------------
- Temperature forecasts
- Rainfall probability
- Weather conditions (clear, rain, hot, cold)
- Demand multipliers based on conditions

============================================================================
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import random

from langchain_core.tools import tool


# =============================================================================
# MOCK WEATHER DATA
# =============================================================================

# Simulated weather conditions for different cities
MOCK_WEATHER_DATA = {
    "mumbai": {
        "current": {"temp": 32, "condition": "humid", "humidity": 85},
        "forecast": [
            {"day": 1, "temp_high": 33, "temp_low": 27, "condition": "rain", "rain_prob": 80},
            {"day": 2, "temp_high": 31, "temp_low": 26, "condition": "heavy_rain", "rain_prob": 95},
            {"day": 3, "temp_high": 30, "temp_low": 25, "condition": "rain", "rain_prob": 70},
            {"day": 4, "temp_high": 32, "temp_low": 26, "condition": "cloudy", "rain_prob": 40},
            {"day": 5, "temp_high": 33, "temp_low": 27, "condition": "clear", "rain_prob": 10},
            {"day": 6, "temp_high": 34, "temp_low": 28, "condition": "hot", "rain_prob": 5},
            {"day": 7, "temp_high": 35, "temp_low": 28, "condition": "very_hot", "rain_prob": 0},
        ]
    },
    "delhi": {
        "current": {"temp": 38, "condition": "very_hot", "humidity": 35},
        "forecast": [
            {"day": 1, "temp_high": 40, "temp_low": 28, "condition": "very_hot", "rain_prob": 0},
            {"day": 2, "temp_high": 41, "temp_low": 29, "condition": "very_hot", "rain_prob": 5},
            {"day": 3, "temp_high": 39, "temp_low": 28, "condition": "hot", "rain_prob": 10},
            {"day": 4, "temp_high": 38, "temp_low": 27, "condition": "hot", "rain_prob": 15},
            {"day": 5, "temp_high": 36, "temp_low": 26, "condition": "clear", "rain_prob": 20},
            {"day": 6, "temp_high": 35, "temp_low": 25, "condition": "cloudy", "rain_prob": 30},
            {"day": 7, "temp_high": 34, "temp_low": 25, "condition": "rain", "rain_prob": 60},
        ]
    },
    "bengaluru": {
        "current": {"temp": 26, "condition": "pleasant", "humidity": 65},
        "forecast": [
            {"day": 1, "temp_high": 28, "temp_low": 20, "condition": "clear", "rain_prob": 15},
            {"day": 2, "temp_high": 27, "temp_low": 19, "condition": "cloudy", "rain_prob": 30},
            {"day": 3, "temp_high": 26, "temp_low": 19, "condition": "rain", "rain_prob": 65},
            {"day": 4, "temp_high": 25, "temp_low": 18, "condition": "rain", "rain_prob": 55},
            {"day": 5, "temp_high": 27, "temp_low": 19, "condition": "cloudy", "rain_prob": 25},
            {"day": 6, "temp_high": 28, "temp_low": 20, "condition": "clear", "rain_prob": 10},
            {"day": 7, "temp_high": 29, "temp_low": 20, "condition": "clear", "rain_prob": 5},
        ]
    },
    "default": {
        "current": {"temp": 30, "condition": "clear", "humidity": 50},
        "forecast": [
            {"day": 1, "temp_high": 31, "temp_low": 22, "condition": "clear", "rain_prob": 10},
            {"day": 2, "temp_high": 32, "temp_low": 23, "condition": "cloudy", "rain_prob": 25},
            {"day": 3, "temp_high": 30, "temp_low": 22, "condition": "rain", "rain_prob": 50},
            {"day": 4, "temp_high": 29, "temp_low": 21, "condition": "clear", "rain_prob": 15},
            {"day": 5, "temp_high": 31, "temp_low": 22, "condition": "clear", "rain_prob": 5},
            {"day": 6, "temp_high": 33, "temp_low": 24, "condition": "hot", "rain_prob": 0},
            {"day": 7, "temp_high": 34, "temp_low": 25, "condition": "hot", "rain_prob": 0},
        ]
    }
}

# Weather condition to demand impact mapping
CONDITION_IMPACTS = {
    "rain": {
        "Umbrellas": 2.5,
        "Raincoats": 2.0,
        "Summer Wear": 0.6,
        "Electronics": 1.0,
        "Home Essentials": 1.0,
        "Winter Wear": 0.8
    },
    "heavy_rain": {
        "Umbrellas": 3.0,
        "Raincoats": 2.5,
        "Summer Wear": 0.5,
        "Electronics": 1.0,
        "Home Essentials": 1.1,
        "Winter Wear": 0.7
    },
    "hot": {
        "Umbrellas": 0.7,
        "Raincoats": 0.3,
        "Summer Wear": 1.8,
        "Electronics": 1.1,
        "Home Essentials": 1.2,
        "Winter Wear": 0.2
    },
    "very_hot": {
        "Umbrellas": 0.5,
        "Raincoats": 0.2,
        "Summer Wear": 2.2,
        "Electronics": 1.2,
        "Home Essentials": 1.4,
        "Winter Wear": 0.1
    },
    "cold": {
        "Umbrellas": 0.8,
        "Raincoats": 0.6,
        "Summer Wear": 0.3,
        "Electronics": 1.0,
        "Home Essentials": 1.1,
        "Winter Wear": 1.8
    },
    "very_cold": {
        "Umbrellas": 0.6,
        "Raincoats": 0.5,
        "Summer Wear": 0.2,
        "Electronics": 0.9,
        "Home Essentials": 1.2,
        "Winter Wear": 2.5
    },
    "clear": {
        "Umbrellas": 0.5,
        "Raincoats": 0.4,
        "Summer Wear": 1.2,
        "Electronics": 1.0,
        "Home Essentials": 1.0,
        "Winter Wear": 0.8
    },
    "cloudy": {
        "Umbrellas": 1.2,
        "Raincoats": 1.0,
        "Summer Wear": 0.9,
        "Electronics": 1.0,
        "Home Essentials": 1.0,
        "Winter Wear": 1.0
    }
}


# =============================================================================
# WEATHER TOOLS
# =============================================================================

@tool
def get_weather_forecast(region: str = "mumbai", days: int = 7) -> str:
    """
    Get weather forecast for a specified region.
    
    Returns temperature, conditions, and rainfall probability.
    This is MOCK DATA for development - will be replaced with real API.
    
    Args:
        region: City name (mumbai, delhi, bengaluru, etc.)
        days: Number of forecast days (1-7)
        
    Returns:
        str: Formatted weather forecast
    """
    # Normalize region name
    region_key = region.lower().strip()
    if region_key not in MOCK_WEATHER_DATA:
        region_key = "default"
    
    weather = MOCK_WEATHER_DATA[region_key]
    current = weather["current"]
    forecast = weather["forecast"][:min(days, 7)]
    
    # Get base date (today)
    today = datetime.now()
    
    result = f"[WEATHER] Weather Forecast for {region.title()}\n"
    result += "=" * 40 + "\n\n"
    
    # Current conditions
    result += f"[CURRENT] Current Conditions:\n"
    result += f"   Temperature: {current['temp']}C\n"
    result += f"   Condition: {current['condition'].replace('_', ' ').title()}\n"
    result += f"   Humidity: {current['humidity']}%\n\n"
    
    # Forecast
    result += f"[FORECAST] {days}-Day Forecast:\n"
    result += "-" * 40 + "\n"
    
    rainy_days = 0
    hot_days = 0
    
    for day in forecast:
        day_date = today + timedelta(days=day['day'])
        day_name = day_date.strftime("%a %d %b")
        condition = day['condition'].replace('_', ' ').title()
        
        # Weather indicator
        if 'rain' in day['condition']:
            emoji = "[RAIN]"
            rainy_days += 1
        elif 'hot' in day['condition']:
            emoji = "[HOT]"
            hot_days += 1
        elif day['condition'] == 'cold' or day['condition'] == 'very_cold':
            emoji = "[COLD]"
        elif day['condition'] == 'cloudy':
            emoji = "[CLOUD]"
        else:
            emoji = "[CLEAR]"
        
        result += (
            f"{emoji} {day_name}: {condition}\n"
            f"   High: {day['temp_high']}C | Low: {day['temp_low']}C\n"
            f"   Rain Probability: {day['rain_prob']}%\n\n"
        )
    
    # Summary
    result += "[SUMMARY]:\n"
    result += f"   Rainy Days: {rainy_days}/{len(forecast)}\n"
    result += f"   Hot Days: {hot_days}/{len(forecast)}\n"
    
    if rainy_days >= 3:
        result += "   [!] ALERT: Extended rain period expected - stock up on rain gear!\n"
    if hot_days >= 3:
        result += "   [!] ALERT: Heat wave expected - increase summer wear inventory!\n"
    
    return result


@tool
def get_weather_impact(region: str = "mumbai", days: int = 7) -> str:
    """
    Calculate how weather will impact product demand.
    
    Returns demand multipliers for each product category based on
    forecasted weather conditions.
    
    Args:
        region: City name for weather forecast
        days: Number of days to analyze
        
    Returns:
        str: Impact analysis with demand multipliers per category
    """
    # Get weather data
    region_key = region.lower().strip()
    if region_key not in MOCK_WEATHER_DATA:
        region_key = "default"
    
    forecast = MOCK_WEATHER_DATA[region_key]["forecast"][:min(days, 7)]
    
    # Calculate average impact per category
    category_impacts: Dict[str, List[float]] = {
        "Umbrellas": [],
        "Raincoats": [],
        "Summer Wear": [],
        "Winter Wear": [],
        "Electronics": [],
        "Home Essentials": []
    }
    
    for day in forecast:
        condition = day['condition']
        if condition not in CONDITION_IMPACTS:
            condition = "clear"  # Default to clear
        
        impacts = CONDITION_IMPACTS.get(condition, CONDITION_IMPACTS["clear"])
        for category, multiplier in impacts.items():
            if category in category_impacts:
                category_impacts[category].append(multiplier)
    
    # Calculate averages and format output
    result = f"[IMPACT] Weather Impact Analysis for {region.title()} ({days} days)\n"
    result += "=" * 50 + "\n\n"
    
    result += "Category Demand Multipliers:\n"
    result += "-" * 50 + "\n"
    
    high_impact = []
    low_impact = []
    
    for category, multipliers in category_impacts.items():
        avg_multiplier = sum(multipliers) / len(multipliers) if multipliers else 1.0
        
        # Format with visual indicator
        if avg_multiplier >= 1.5:
            indicator = "[^] HIGH DEMAND"
            high_impact.append((category, avg_multiplier))
        elif avg_multiplier <= 0.6:
            indicator = "[v] LOW DEMAND"
            low_impact.append((category, avg_multiplier))
        else:
            indicator = "[-] NORMAL"
        
        result += f"{category:20} | {avg_multiplier:.2f}x | {indicator}\n"
    
    result += "\n"
    
    # Recommendations
    if high_impact:
        result += "[PRIORITY] PRIORITIZE RESTOCKING:\n"
        for cat, mult in sorted(high_impact, key=lambda x: -x[1]):
            result += f"   * {cat}: {mult:.1f}x expected demand increase\n"
        result += "\n"
    
    if low_impact:
        result += "[REDUCE] REDUCE ORDERS FOR:\n"
        for cat, mult in sorted(low_impact, key=lambda x: x[1]):
            result += f"   * {cat}: Only {mult:.1f}x normal demand expected\n"
    
    return result
