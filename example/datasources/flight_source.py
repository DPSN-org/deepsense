"""
Flight DataSource implementation for example
"""

import os
import requests
from deepsense import DataSource, DataSourceConfig, tool
from typing import Dict, Any

class FlightDataSource(DataSource):
    """Flight data source using Amadeus API."""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AMADEUS_CLIENT_SECRET")
        
        config = DataSourceConfig(
            name="flight",
            rest_url="https://test.api.amadeus.com/v2",
            headers={"Content-Type": "application/json"}
        )
        super().__init__(config)
        self._token = None
    
    def _get_token(self) -> str:
        """Get Amadeus access token."""
        if self._token:
            return self._token
        
        if not self.client_id or not self.client_secret:
            return ""
        
        try:
            url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            self._token = response.json()["access_token"]
            return self._token
        except:
            return ""
    
    @tool(name="find_flights", description="Find available flights between two cities on a specific date. Use get_location_codes first if city names are provided.")
    def find_flights(self, origin: str, destination: str, date: str) -> Dict[str, Any]:
        """Find flights between two cities."""
        token = self._get_token()
        if not token:
            return self._get_mock_flights(origin, destination, date)
        
        # Check if inputs look like city names
        if self._is_likely_city_name(origin) or self._is_likely_city_name(destination):
            return {
                "suggestion": "Please use get_location_codes tool first to find IATA codes",
                "origin": origin,
                "destination": destination,
                "date": date
            }
        
        # Use custom session with token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {
            "originLocationCode": origin.upper(),
            "destinationLocationCode": destination.upper(),
            "departureDate": date,
            "adults": 1,
            "max": 10
        }
        
        try:
            url = f"{self.config.rest_url}/shopping/flight-offers"
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            flights = []
            for offer in data.get("data", []):
                flight = {
                    "id": offer["id"],
                    "price": offer["price"],
                    "itineraries": offer["itineraries"]
                }
                flights.append(flight)
            
            return {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "date": date,
                "flights": flights,
                "total_count": len(flights)
            }
        except:
            return self._get_mock_flights(origin, destination, date)
    
    def _is_likely_city_name(self, text: str) -> bool:
        """Check if text looks like a city name."""
        if len(text) == 3 and text.isalpha() and text.isupper():
            return False
        if ' ' in text or len(text) > 3 and not text.isupper():
            return True
        return False
    
    def _get_mock_flights(self, origin: str, destination: str, date: str) -> Dict[str, Any]:
        """Return mock flight data."""
        import random
        random.seed(hash(f"{origin}{destination}{date}") % 1000)
        airlines = ["AA", "UA", "DL", "BA", "LH"]
        flights = []
        for i in range(5):
            flights.append({
                "id": f"mock_flight_{i}",
                "price": {"total": str(random.randint(200, 1500)), "currency": "USD"},
                "itineraries": [{
                    "duration": f"PT{random.randint(1, 8)}H",
                    "segments": [{
                        "departure": {"airport": origin.upper(), "time": f"{date}T{random.randint(6, 22):02d}:00:00"},
                        "arrival": {"airport": destination.upper(), "time": f"{date}T{random.randint(6, 22):02d}:00:00"},
                        "carrier": random.choice(airlines),
                        "flight_number": f"{random.choice(airlines)}{random.randint(100, 9999)}"
                    }]
                }]
            })
        return {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "date": date,
            "flights": flights,
            "total_count": len(flights),
            "note": "This is mock data. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET for real data."
        }
    
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        try:
            result = self.find_flights("JFK", "LAX", "2024-12-01")
            return "error" not in result
        except:
            return False

