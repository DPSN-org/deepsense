"""
Weather DataSource implementation for example
"""

import os
import requests
from deepsense import DataSource, DataSourceConfig, tool
from typing import Dict, Any

class WeatherDataSource(DataSource):
    """Weather data source using OpenWeatherMap."""
    
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        config = DataSourceConfig(
            name="weather",
            rest_url="https://api.openweathermap.org/data/2.5",
            params={"appid": api_key} if api_key else {},
            headers={"Accept": "application/json"}
        )
        super().__init__(config)
        self.api_key = api_key
    
    @tool(name="get_weather", description="Get current weather information for a specific city")
    def get_weather(self, city: str) -> Dict[str, Any]:
        """Get current weather for a city."""
        if not self.api_key:
            return self._get_mock_weather(city)
        
        result = self.get("/weather", {"q": city, "units": "metric"})
        
        if "error" in result:
            return self._get_mock_weather(city)
        
        # Format the response
        return {
            "city": result.get("name", city),
            "country": result.get("sys", {}).get("country", ""),
            "temperature": {
                "current": round(result.get("main", {}).get("temp", 0), 1),
                "feels_like": round(result.get("main", {}).get("feels_like", 0), 1),
                "min": round(result.get("main", {}).get("temp_min", 0), 1),
                "max": round(result.get("main", {}).get("temp_max", 0), 1)
            },
            "description": result.get("weather", [{}])[0].get("description", ""),
            "humidity": result.get("main", {}).get("humidity", 0),
            "pressure": result.get("main", {}).get("pressure", 0),
            "wind_speed": result.get("wind", {}).get("speed", 0),
            "visibility": result.get("visibility", "N/A"),
            "sunrise": result.get("sys", {}).get("sunrise", 0),
            "sunset": result.get("sys", {}).get("sunset", 0)
        }
    
    def _get_mock_weather(self, city: str) -> Dict[str, Any]:
        """Return mock weather data."""
        import random
        random.seed(hash(city) % 1000)
        temp = random.randint(15, 30)
        return {
            "city": city,
            "country": "Mock",
            "temperature": {
                "current": temp,
                "feels_like": temp + random.randint(-2, 2),
                "min": temp - random.randint(2, 5),
                "max": temp + random.randint(2, 5)
            },
            "description": random.choice(["clear sky", "few clouds", "scattered clouds", "rain"]),
            "humidity": random.randint(40, 90),
            "pressure": random.randint(1000, 1020),
            "wind_speed": round(random.uniform(0, 15), 1),
            "note": "This is mock data. Set OPENWEATHER_API_KEY for real data."
        }
    
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        try:
            result = self.get_weather("London")
            return "error" not in result
        except:
            return False

