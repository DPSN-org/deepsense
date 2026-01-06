"""
User-defined datasources for the example
"""

from .crypto_source import CryptoDataSource
from .github_source import GitHubDataSource
from .helius_source import HeliusDataSource
from .jupiter_source import JupiterDataSource
from .weather_source import WeatherDataSource
from .flight_source import FlightDataSource
from .location_source import LocationDataSource
from .dpsn_source import DPSNDataSource
from .coingecko_source import CoinGeckoDataSource
from .news_source import NewsDataSource

__all__ = [
    "CryptoDataSource",
    "GitHubDataSource",
    "HeliusDataSource",
    "JupiterDataSource",
    "WeatherDataSource",
    "FlightDataSource",
    "LocationDataSource",
    "DPSNDataSource",
    "CoinGeckoDataSource",
    "NewsDataSource"
]

