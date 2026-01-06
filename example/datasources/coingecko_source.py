"""
CoinGecko DataSource implementation for example
"""

from deepsense import DataSource, DataSourceConfig, tool
from typing import Dict, Any, Optional

class CoinGeckoDataSource(DataSource):
    """CoinGecko cryptocurrency data source."""
    
    def __init__(self):
        config = DataSourceConfig(
            name="coingecko",
            rest_url="https://api.coingecko.com/api/v3",
            headers={"Accept": "application/json"}
        )
        super().__init__(config)
    
    @tool(name="coingecko_data", description="Unified tool for accessing CoinGecko cryptocurrency data. Supports price, market data, trending, history, search, and more.")
    def get_coin_price(self, coin_id: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """Get current price and market data for a specific cryptocurrency."""
        return self.get("/simple/price", {"ids": coin_id, "vs_currencies": vs_currency, 
                                          "include_market_cap": "true", "include_24hr_vol": "true"})
    
    @tool(name="coingecko_data")
    def get_coin_market_data(self, coin_id: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """Get detailed market data for a specific cryptocurrency."""
        return self.get("/coins/markets", {"vs_currency": vs_currency, "ids": coin_id, 
                                          "order": "market_cap_desc", "per_page": 1, "page": 1})
    
    @tool(name="coingecko_data")
    def get_trending_coins(self) -> Dict[str, Any]:
        """Get trending coins in the last 24 hours."""
        return self.get("/search/trending")
    
    @tool(name="coingecko_data")
    def get_coin_history(self, coin_id: str, date: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """Get historical price data for a specific date."""
        return self.get(f"/coins/{coin_id}/history", {"date": date, "localization": False})
    
    @tool(name="coingecko_data")
    def get_coin_market_chart(self, coin_id: str, vs_currency: str = "usd", days: int = 30) -> Dict[str, Any]:
        """Get market chart data for a cryptocurrency."""
        return self.get(f"/coins/{coin_id}/market_chart", {"vs_currency": vs_currency, "days": days})
    
    @tool(name="coingecko_data")
    def get_exchange_rates(self) -> Dict[str, Any]:
        """Get exchange rates."""
        return self.get("/exchange_rates")
    
    @tool(name="coingecko_data")
    def get_global_data(self) -> Dict[str, Any]:
        """Get global cryptocurrency market data."""
        return self.get("/global")
    
    @tool(name="coingecko_data")
    def search_coins(self, query: str) -> Dict[str, Any]:
        """Search for coins by name, symbol, or keyword."""
        return self.get("/search", {"query": query})
    
    @tool(name="coingecko_data")
    def get_coin_info(self, coin_id: str) -> Dict[str, Any]:
        """Get comprehensive information for a specific coin."""
        return self.get(f"/coins/{coin_id}", {"localization": False, "tickers": False, 
                                             "market_data": True, "community_data": False, 
                                             "developer_data": False})
    
    @tool(name="coingecko_data")
    def get_top_coins(self, vs_currency: str = "usd", order: str = "market_cap_desc", 
                     per_page: int = 100, page: int = 1) -> Dict[str, Any]:
        """Get top cryptocurrencies by market cap."""
        return self.get("/coins/markets", {"vs_currency": vs_currency, "order": order, 
                                          "per_page": per_page, "page": page})
    
    @tool(name="coingecko_data")
    def get_exchanges(self) -> Dict[str, Any]:
        """Get list of cryptocurrency exchanges."""
        return self.get("/exchanges")
    
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        try:
            result = self.get("/ping")
            return "gecko_says" in str(result)
        except:
            return False

