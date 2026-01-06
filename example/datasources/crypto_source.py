"""
Example Crypto DataSource implementation
"""

from deepsense import DataSource, DataSourceConfig
from typing import Dict, Any
from datetime import datetime

class CryptoDataSource(DataSource):
    """Example cryptocurrency data source."""
    
    def __init__(self, api_key: str = None):
        config = DataSourceConfig(
            name="crypto",
            rest_url="https://api.coingecko.com/api/v3",
            headers={"Accept": "application/json"}
        )
        super().__init__(config)
        self.api_key = api_key
    
    def get_coin_price(self, coin_id: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """Get current price of a cryptocurrency."""
        return self.get(f"/simple/price", params={"ids": coin_id, "vs_currencies": vs_currency})
    
    def get_coin_quote(self, coin_id: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """
        Get cryptocurrency price quote with user_action flag.
        This will be detected by the workflow and added to user_actions.
        """
        data = self.get_coin_price(coin_id, vs_currency)
        return {
            "user_action": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "source": self.config.name,
            "action_type": "price_quote"
        }
    
    def health_check(self) -> bool:
        """Check if the data source is accessible."""
        try:
            result = self.get("/ping")
            return "gecko_says" in str(result)
        except:
            return False

