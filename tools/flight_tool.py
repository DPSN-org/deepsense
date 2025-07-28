import requests
import json
from typing import Dict, Any, List
from datetime import datetime
from config import config

def find_flights(origin: str, destination: str, date: str) -> Dict[str, Any]:
    """
    Find available flights between two cities on a specific date.
    
    Args:
        origin (str): Origin city/airport code or city name
        destination (str): Destination city/airport code or city name
        date (str): Travel date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Flight information including available flights, prices, etc.
        
    Note: If city names are provided instead of IATA codes, the tool will suggest
    using the get_location_codes tool first to find the appropriate codes.
    """
    try:
        # Check if inputs look like city names rather than IATA codes
        origin_is_city = _is_likely_city_name(origin)
        destination_is_city = _is_likely_city_name(destination)
        
        if origin_is_city or destination_is_city:
            return {
                "suggestion": "Please use the get_location_codes tool first to find IATA codes",
                "origin": origin,
                "destination": destination,
                "date": date,
                "origin_needs_code": origin_is_city,
                "destination_needs_code": destination_is_city,
                "message": f"City names detected. Please search for IATA codes using get_location_codes tool for: {origin if origin_is_city else ''} {destination if destination_is_city else ''}".strip()
            }
        
        # If no API credentials are provided, return mock data
        if not config.AMADEUS_CLIENT_ID or not config.AMADEUS_CLIENT_SECRET:
            return _get_mock_flights(origin, destination, date)
        
        # Get access token
        token = _get_amadeus_token()
        print(token)
        if not token:
            return _get_mock_flights(origin, destination, date)
        
        # Search for flights using v2 API
        url = f"{config.AMADEUS_BASE_URL}/shopping/flight-offers"
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
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
            
        data = response.json()
        print(response)
        print(data)
        # Process flight data
        flights = []
        for offer in data.get("data", []):
            flight = {
                "id": offer["id"],
                "price": {
                    "total": offer["price"]["total"],
                    "currency": offer["price"]["currency"]
                },
                "itineraries": []
            }
            
            for itinerary in offer["itineraries"]:
                segments = []
                for segment in itinerary["segments"]:
                    segments.append({
                        "departure": {
                            "airport": segment["departure"]["iataCode"],
                            "time": segment["departure"]["at"]
                        },
                        "arrival": {
                            "airport": segment["arrival"]["iataCode"],
                            "time": segment["arrival"]["at"]
                        },
                        "carrier": segment["carrierCode"],
                        "flight_number": segment["number"],
                        "duration": segment["duration"]
                    })
                
                flight["itineraries"].append({
                    "duration": itinerary["duration"],
                    "segments": segments
                })
            
            flights.append(flight)
        print(flights)
        return {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "date": date,
            "flights": flights,
            "total_count": len(flights)
        }
        
    except requests.RequestException as e:
        return {
            "error": f"Failed to fetch flight data: {str(e)}",
            "origin": origin,
            "destination": destination,
            "date": date,
            "fallback": _get_mock_flights(origin, destination, date)
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "origin": origin,
            "destination": destination,
            "date": date,
            "fallback": _get_mock_flights(origin, destination, date)
        }

def _is_likely_city_name(text: str) -> bool:
    """Check if the text looks like a city name rather than an IATA code."""
    # IATA codes are typically 3 letters
    if len(text) == 3 and text.isalpha() and text.isupper():
        return False
    
    # If it contains spaces, it's likely a city name
    if ' ' in text:
        return True
    
    # If it's longer than 3 characters and not all uppercase, likely a city name
    if len(text) > 3 and not text.isupper():
        return True
    
    # Common city names that might be confused with codes
    common_cities = ['london', 'paris', 'tokyo', 'new york', 'los angeles', 'san francisco', 
                     'chicago', 'miami', 'boston', 'seattle', 'denver', 'atlanta',
                     'delhi', 'mumbai', 'bangalore', 'chennai', 'kolkata', 'hyderabad',
                     'dubai', 'abu dhabi', 'doha', 'riyadh', 'jeddah', 'muscat']
    
    return text.lower() in common_cities

def _get_amadeus_token() -> str:
    """Get access token from Amadeus API."""
    try:
        # Token endpoint is still v1
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

def _get_mock_flights(origin: str, destination: str, date: str) -> Dict[str, Any]:
    """Return mock flight data for demonstration purposes."""
    import random
    
    # Generate consistent mock data based on route and date
    random.seed(hash(f"{origin}{destination}{date}") % 1000)
    
    airlines = ["AA", "UA", "DL", "BA", "LH", "AF", "EK", "QR", "TK", "SQ"]
    flight_numbers = [f"{random.choice(airlines)}{random.randint(100, 9999)}" for _ in range(5)]
    
    flights = []
    for i, flight_num in enumerate(flight_numbers):
        # Generate departure and arrival times
        departure_hour = random.randint(6, 22)
        flight_duration = random.randint(1, 8)
        arrival_hour = (departure_hour + flight_duration) % 24
        
        departure_time = f"{date}T{departure_hour:02d}:{random.randint(0, 59):02d}:00"
        arrival_time = f"{date}T{arrival_hour:02d}:{random.randint(0, 59):02d}:00"
        
        # Generate price
        base_price = random.randint(200, 1500)
        price = base_price + random.randint(-50, 100)
        
        flight = {
            "id": f"mock_flight_{i}",
            "price": {
                "total": str(price),
                "currency": "USD"
            },
            "itineraries": [{
                "duration": f"PT{flight_duration}H",
                "segments": [{
                    "departure": {
                        "airport": origin.upper(),
                        "time": departure_time
                    },
                    "arrival": {
                        "airport": destination.upper(),
                        "time": arrival_time
                    },
                    "carrier": flight_num[:2],
                    "flight_number": flight_num,
                    "duration": f"PT{flight_duration}H"
                }]
            }]
        }
        flights.append(flight)
    
    return {
        "origin": origin.upper(),
        "destination": destination.upper(),
        "date": date,
        "flights": flights,
        "total_count": len(flights),
        "note": "This is mock data. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET for real data."
    }

# Tool schema for LangGraph registration
FLIGHT_TOOL_SCHEMA = {
    "name": "find_flights",
    "description": "Search for available flights between two cities on a specific date. If city names are provided, use get_location_codes tool first to find IATA codes.",
    "parameters": {
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "description": "Origin city name or airport IATA code (e.g., 'London' or 'LHR')"
            },
            "destination": {
                "type": "string",
                "description": "Destination city name or airport IATA code (e.g., 'Paris' or 'CDG')"
            },
            "date": {
                "type": "string",
                "description": "Travel date in YYYY-MM-DD format (e.g., '2024-07-22')"
            }
        },
        "required": ["origin", "destination", "date"]
    }
} 