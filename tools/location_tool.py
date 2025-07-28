import requests
import json
from typing import Dict, Any, List
from config import config

def get_location_codes(keyword: str, sub_type: str = "CITY,AIRPORT") -> Dict[str, Any]:
    """
    Get location codes for airports and cities using Amadeus API.
    
    Args:
        keyword (str): Search keyword (city name, airport name, etc.)
        sub_type (str): Type of locations to search for (CITY, AIRPORT, or both)
        
    Returns:
        Dict[str, Any]: Location information including codes, names, and details
    """
    try:
        # If no API credentials are provided, return mock data
        if not config.AMADEUS_CLIENT_ID or not config.AMADEUS_CLIENT_SECRET:
            return _get_mock_locations(keyword, sub_type)
        
        # Get access token
        token = _get_amadeus_token()
        if not token:
            return _get_mock_locations(keyword, sub_type)
        
        # Search for locations
        url = "https://test.api.amadeus.com/v1/reference-data/locations"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {
            "subType": sub_type,
            "keyword": keyword
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Process location data
        locations = []
        for location in data.get("data", []):
            location_info = {
                "name": location.get("name", ""),
                "iata_code": location.get("iataCode", ""),
                "sub_type": location.get("subType", ""),
                "country_code": location.get("address", {}).get("countryCode", ""),
                "country_name": location.get("address", {}).get("countryName", ""),
                "city_name": location.get("address", {}).get("cityName", ""),
                "city_code": location.get("address", {}).get("cityCode", ""),
                "region_code": location.get("address", {}).get("regionCode", ""),
                "timezone": location.get("timeZoneOffset", ""),
                "geo_code": {
                    "latitude": location.get("geoCode", {}).get("latitude", ""),
                    "longitude": location.get("geoCode", {}).get("longitude", "")
                }
            }
            locations.append(location_info)
        
        return {
            "keyword": keyword,
            "sub_type": sub_type,
            "locations": locations,
            "total_count": len(locations)
        }
        
    except requests.RequestException as e:
        return {
            "error": f"Failed to fetch location data: {str(e)}",
            "keyword": keyword,
            "sub_type": sub_type,
            "fallback": _get_mock_locations(keyword, sub_type)
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "keyword": keyword,
            "sub_type": sub_type,
            "fallback": _get_mock_locations(keyword, sub_type)
        }

def _get_amadeus_token() -> str:
    """Get access token from Amadeus API."""
    try:
        # Token endpoint is v1
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": config.AMADEUS_CLIENT_ID,
            "client_secret": config.AMADEUS_CLIENT_SECRET
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data["access_token"]
        
    except Exception as e:
        print(f"Failed to get Amadeus token: {e}")
        return ""

def _get_mock_locations(keyword: str, sub_type: str) -> Dict[str, Any]:
    """Return mock location data for demonstration purposes."""
    import random
    
    # Generate consistent mock data based on keyword
    random.seed(hash(keyword.lower()) % 1000)
    
    # Common location mappings for popular cities
    location_mappings = {
        "london": [
            {"name": "London Heathrow Airport", "iata_code": "LHR", "sub_type": "AIRPORT", "city_name": "London", "country_code": "GB"},
            {"name": "London Gatwick Airport", "iata_code": "LGW", "sub_type": "AIRPORT", "city_name": "London", "country_code": "GB"},
            {"name": "London", "iata_code": "LON", "sub_type": "CITY", "city_name": "London", "country_code": "GB"}
        ],
        "paris": [
            {"name": "Paris Charles de Gaulle Airport", "iata_code": "CDG", "sub_type": "AIRPORT", "city_name": "Paris", "country_code": "FR"},
            {"name": "Paris Orly Airport", "iata_code": "ORY", "sub_type": "AIRPORT", "city_name": "Paris", "country_code": "FR"},
            {"name": "Paris", "iata_code": "PAR", "sub_type": "CITY", "city_name": "Paris", "country_code": "FR"}
        ],
        "new york": [
            {"name": "New York John F. Kennedy Airport", "iata_code": "JFK", "sub_type": "AIRPORT", "city_name": "New York", "country_code": "US"},
            {"name": "New York LaGuardia Airport", "iata_code": "LGA", "sub_type": "AIRPORT", "city_name": "New York", "country_code": "US"},
            {"name": "New York", "iata_code": "NYC", "sub_type": "CITY", "city_name": "New York", "country_code": "US"}
        ],
        "tokyo": [
            {"name": "Tokyo Haneda Airport", "iata_code": "HND", "sub_type": "AIRPORT", "city_name": "Tokyo", "country_code": "JP"},
            {"name": "Tokyo Narita Airport", "iata_code": "NRT", "sub_type": "AIRPORT", "city_name": "Tokyo", "country_code": "JP"},
            {"name": "Tokyo", "iata_code": "TYO", "sub_type": "CITY", "city_name": "Tokyo", "country_code": "JP"}
        ],
        "delhi": [
            {"name": "Delhi Indira Gandhi Airport", "iata_code": "DEL", "sub_type": "AIRPORT", "city_name": "Delhi", "country_code": "IN"},
            {"name": "Delhi", "iata_code": "DEL", "sub_type": "CITY", "city_name": "Delhi", "country_code": "IN"}
        ],
        "dubai": [
            {"name": "Dubai International Airport", "iata_code": "DXB", "sub_type": "AIRPORT", "city_name": "Dubai", "country_code": "AE"},
            {"name": "Dubai", "iata_code": "DXB", "sub_type": "CITY", "city_name": "Dubai", "country_code": "AE"}
        ]
    }
    
    # Check if we have predefined data for this keyword
    keyword_lower = keyword.lower()
    if keyword_lower in location_mappings:
        locations = location_mappings[keyword_lower]
    else:
        # Generate generic mock data
        locations = []
        for i in range(random.randint(1, 3)):
            location_type = random.choice(["AIRPORT", "CITY"])
            if location_type == "AIRPORT":
                name = f"{keyword.title()} Airport"
                iata_code = keyword[:3].upper() + str(random.randint(1, 9))
            else:
                name = keyword.title()
                iata_code = keyword[:3].upper()
            
            locations.append({
                "name": name,
                "iata_code": iata_code,
                "sub_type": location_type,
                "city_name": keyword.title(),
                "country_code": random.choice(["US", "GB", "FR", "DE", "JP", "IN", "AE", "CA", "AU"])
            })
    
    # Filter by sub_type if specified
    if sub_type != "CITY,AIRPORT":
        sub_types = sub_type.split(",")
        locations = [loc for loc in locations if loc["sub_type"] in sub_types]
    
    # Add additional mock fields
    for location in locations:
        location.update({
            "country_name": _get_country_name(location["country_code"]),
            "city_code": location["iata_code"],
            "region_code": "",
            "timezone": random.choice(["+00:00", "+01:00", "+05:30", "+09:00", "-05:00"]),
            "geo_code": {
                "latitude": round(random.uniform(-90, 90), 4),
                "longitude": round(random.uniform(-180, 180), 4)
            }
        })
    
    return {
        "keyword": keyword,
        "sub_type": sub_type,
        "locations": locations,
        "total_count": len(locations),
        "note": "This is mock data. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET for real data."
    }

def _get_country_name(country_code: str) -> str:
    """Get country name from country code."""
    country_names = {
        "US": "United States",
        "GB": "United Kingdom",
        "FR": "France",
        "DE": "Germany",
        "JP": "Japan",
        "IN": "India",
        "AE": "United Arab Emirates",
        "CA": "Canada",
        "AU": "Australia"
    }
    return country_names.get(country_code, "Unknown")

# Tool schema for LangGraph registration
LOCATION_TOOL_SCHEMA = {
    "name": "get_location_codes",
    "description": "Search for airport and city codes using keywords. Use this tool before find_flights when you need to convert city names to IATA codes.",
    "parameters": {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "Search keyword (city name, airport name, etc.)"
            },
            "sub_type": {
                "type": "string",
                "description": "Type of locations to search for: CITY, AIRPORT, or CITY,AIRPORT (default)",
                "default": "CITY,AIRPORT"
            }
        },
        "required": ["keyword"]
    }
} 