"""
Helius Data Source for LangGraph Assistant
Provides unified access to multiple blockchain networks and data types.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional, Union
from .core import DataSource, DataSourceConfig
import logging

logger = logging.getLogger(__name__)

class HeliusDataSource(DataSource):
    """Unified data source for Helius API - Solana blockchain data."""
    
    def __init__(self, api_key: str, network: str = "mainnet-beta"):
        config = DataSourceConfig(
            name="helius",
            rest_url="https://api.helius.xyz/v0",
            rpc_url="https://mainnet.helius-rpc.com",
            params={"api-key": api_key},
            headers={"Content-Type": "application/json"}
        )
        super().__init__(config)
        self.api_key = api_key
        self.network = network
    
    def health_check(self) -> bool:
        """Check if the Helius API is accessible."""
        try:
            # Test REST API
            response = self.session.get("https://api.helius.xyz/v0/addresses/11111111111111111111111111111112/transactions?limit=1", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            return False
    
    # --- REST Methods (Enhanced API) ---
    def get_enhanced_transactions_by_address(self, address: str, limit: int = 100, before: Optional[str] = None, until: Optional[str] = None, commitment: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"addresses/{address}/transactions"
        params = {"limit": limit}
        if before: params["before"] = before
        if until: params["until"] = until
        if commitment: params["commitment"] = commitment
        return self.get(endpoint, params)

    # --- RPC Methods (Solana JSON-RPC & DAS) ---
    def get_account_info(self, address: str) -> Dict[str, Any]:
        return self.rpc_post("getAccountInfo", [address, {"encoding": "jsonParsed"}])

    def get_token_accounts(self, address: str) -> Dict[str, Any]:
        return self.rpc_post("getTokenAccountsByOwner", [address, {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}, {"encoding": "jsonParsed"}])

    def get_nft_accounts(self, address: str, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        params = {
            "ownerAddress": address,
            "page": page,
            "limit": limit,
            "sortBy": {
                "sortBy": "created",
                "sortDirection": "asc"
            },
            "options": {
                "showUnverifiedCollections": False,
                "showCollectionMetadata": False,
                "showGrandTotal": False,
                "showFungible": False,
                "showNativeBalance": False,
                "showInscription": False,
                "showZeroBalance": False
            }
        }
        return self.rpc_post("getAssetsByOwner", params)

    def get_transaction_history(self, address: str, limit: int = 100) -> Dict[str, Any]:
        return self.rpc_post("getSignaturesForAddress", [address, {"limit": limit}])

    def get_token_metadata(self, mint_address: str) -> Dict[str, Any]:
        return self.rpc_post("getAsset", {"id": mint_address})

    def get_nft_metadata(self, mint_address: str) -> Dict[str, Any]:
        return self.rpc_post("getAsset", {"id": mint_address})

    def get_asset_by_id(self, asset_id: str) -> Dict[str, Any]:
        return self.rpc_post("getAsset", {"id": asset_id})

    def get_assets_by_group(self, group_key: str, group_value: str, page: int = 1) -> Dict[str, Any]:
        return self.rpc_post("getAssetsByGroup", {"groupKey": group_key, "groupValue": group_value, "page": page})

    def get_assets_by_owner(self, owner_address: str, page: int = 1) -> Dict[str, Any]:
        return self.rpc_post("getAssetsByOwner", {"ownerAddress": owner_address, "page": page})

    def get_asset_search(self, query: str, page: int = 1) -> Dict[str, Any]:
        return self.rpc_post("searchAssets", {"query": query, "page": page})

    def get_balance(self, address: str) -> Dict[str, Any]:
        return self.rpc_post("getBalance", [address])

    def get_token_balance(self, address: str, mint_address: str) -> Dict[str, Any]:
        # This requires the token account address, not the mint address
        # You may need to use getTokenAccountsByOwner first to get the token account
        return self.rpc_post("getTokenAccountBalance", [mint_address])

    def get_parsed_transactions(self, transactions: List[str]) -> Dict[str, Any]:
        """Get parsed transaction details for a list of transaction signatures using the REST API."""
        data = {"transactions": transactions}
        return self.post("transactions", data)

    def get_das_search(self, query: str, limit: int = 100) -> Dict[str, Any]:
        return self.rpc_post("searchAssets", {"query": query, "limit": limit})

# Factory function for Helius data source
def create_helius_source(api_key: str, network: str = "mainnet-beta") -> HeliusDataSource:
    """Create a Helius data source instance."""
    return HeliusDataSource(api_key, network) 