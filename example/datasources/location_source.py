"""
Location DataSource implementation for example
"""

import os
import requests
from deepsense import DataSource, DataSourceConfig, tool
from typing import Dict, Any

class LocationDataSource(DataSource):
    """Location data source using Amadeus API."""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AMADEUS_CLIENT_SECRET")
        
        config = DataSourceConfig(
            name="location",
            rest_url="https://test.api.amadeus.com/v1",
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
    
    @tool(name="get_location_codes", description="Get location codes for airports and cities using a keyword. Use this before find_flights when you need IATA codes.")
    def get_location_codes(self, keyword: str, sub_type: str = "CITY,AIRPORT") -> Dict[str, Any]:
        """Get location codes for airports and cities."""
        token = self._get_token()
        if not token:
            return self._get_mock_locations(keyword, sub_type)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {
            "subType": sub_type,
            "keyword": keyword
        }
        
        try:
            url = f"{self.config.rest_url}/reference-data/locations"
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            locations = []
            for location in data.get("data", []):
                locations.append({
                    "name": location.get("name", ""),
                    "iata_code": location.get("iataCode", ""),
                    "sub_type": location.get("subType", ""),
                    "country_code": location.get("address", {}).get("countryCode", ""),
                    "city_name": location.get("address", {}).get("cityName", "")
                })
            
            return {
                "keyword": keyword,
                "sub_type": sub_type,
                "locations": locations,
                "total_count": len(locations)
            }
        except:
            return self._get_mock_locations(keyword, sub_type)
    
    def _get_mock_locations(self, keyword: str, sub_type: str) -> Dict[str, Any]:
        """Return mock location data."""
        import random
        random.seed(hash(keyword.lower()) % 1000)
        
        location_mappings = {
            "london": [
                {"name": "London Heathrow Airport", "iata_code": "LHR", "sub_type": "AIRPORT", "city_name": "London", "country_code": "GB"},
                {"name": "London", "iata_code": "LON", "sub_type": "CITY", "city_name": "London", "country_code": "GB"}
            ],
            "paris": [
                {"name": "Paris Charles de Gaulle Airport", "iata_code": "CDG", "sub_type": "AIRPORT", "city_name": "Paris", "country_code": "FR"},
                {"name": "Paris", "iata_code": "PAR", "sub_type": "CITY", "city_name": "Paris", "country_code": "FR"}
            ]
        }
        
        keyword_lower = keyword.lower()
        if keyword_lower in location_mappings:
            locations = location_mappings[keyword_lower]
        else:
            locations = [{
                "name": keyword.title(),
                "iata_code": keyword[:3].upper(),
                "sub_type": "CITY",
                "city_name": keyword.title(),
                "country_code": "US"
            }]
        
        if sub_type != "CITY,AIRPORT":
            sub_types = sub_type.split(",")
            locations = [loc for loc in locations if loc["sub_type"] in sub_types]
        
        return {
            "keyword": keyword,
            "sub_type": sub_type,
            "locations": locations,
            "total_count": len(locations),
            "note": "This is mock data. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET for real data."
        }
    
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        try:
            result = self.get_location_codes("London")
            return "error" not in result
        except:
            return False

