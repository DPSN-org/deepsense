import requests
import json
from typing import Dict, Any
from config import config

def get_weather(city: str) -> Dict[str, Any]:
    """
    Get current weather information for a given city.
    
    Args:
        city (str): The city name to get weather for
        
    Returns:
        Dict[str, Any]: Weather information including temperature, description, humidity, etc.
    """
    try:
        # If no API key is provided, return mock data
        if not config.OPENWEATHER_API_KEY:
            return _get_mock_weather(city)
        
        # Make API request to OpenWeatherMap
        url = f"{config.OPENWEATHER_BASE_URL}/weather"
        params = {
            "q": city,
            "appid": config.OPENWEATHER_API_KEY,
            "units": "metric"  # Use Celsius
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract relevant information
        weather_info = {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature": {
                "current": round(data["main"]["temp"], 1),
                "feels_like": round(data["main"]["feels_like"], 1),
                "min": round(data["main"]["temp_min"], 1),
                "max": round(data["main"]["temp_max"], 1)
            },
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "visibility": data.get("visibility", "N/A"),
            "sunrise": data["sys"]["sunrise"],
            "sunset": data["sys"]["sunset"]
        }
        
        return weather_info
        
    except requests.RequestException as e:
        return {
            "error": f"Failed to fetch weather data: {str(e)}",
            "city": city,
            "fallback": _get_mock_weather(city)
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "city": city,
            "fallback": _get_mock_weather(city)
        }

def _get_mock_weather(city: str) -> Dict[str, Any]:
    """Return mock weather data for demonstration purposes."""
    import random
    
    # Generate consistent mock data based on city name
    random.seed(hash(city) % 1000)
    
    temp = random.randint(15, 30)
    weather_conditions = [
        "clear sky", "few clouds", "scattered clouds", "broken clouds",
        "shower rain", "rain", "thunderstorm", "snow", "mist"
    ]
    
    return {
        "city": city,
        "country": "Mock",
        "temperature": {
            "current": temp,
            "feels_like": temp + random.randint(-2, 2),
            "min": temp - random.randint(2, 5),
            "max": temp + random.randint(2, 5)
        },
        "description": random.choice(weather_conditions),
        "humidity": random.randint(40, 90),
        "pressure": random.randint(1000, 1020),
        "wind_speed": round(random.uniform(0, 15), 1),
        "visibility": random.randint(5000, 10000),
        "sunrise": 1640995200,  # Mock timestamp
        "sunset": 1641038400,   # Mock timestamp
        "note": "This is mock data. Set OPENWEATHER_API_KEY for real data."
    }

# Tool schema for LangGraph registration
WEATHER_TOOL_SCHEMA = {
    "name": "get_weather",
    "description": "Get current weather information for a specific city",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The name of the city to get weather information for"
            }
        },
        "required": ["city"]
    }
} 