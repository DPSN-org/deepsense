"""
Helius Data Source for LangGraph Assistant
Provides unified access to multiple blockchain networks and data types.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional, Union
from .core import RESTDataSource, DataSourceConfig
import logging

logger = logging.getLogger(__name__)

class HeliusDataSource:
    """Unified data source for Helius API - Solana blockchain data."""
    def __init__(self, api_key: str, network: str = "mainnet-beta"):
        self.api_key = api_key
        self.network = network
        self.rest_base_url = "https://api.helius.xyz/v0"
        self.rpc_url = "https://mainnet.helius-rpc.com"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.params.update({"api-key": self.api_key})
    # --- Helper for REST GET ---
    def _rest_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.rest_base_url}/{endpoint}"
        # if params is None:
        #     params = {}
        # params["api-key"] = self.api_key
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Helius REST API GET request failed: {e}")
            return {"error": str(e), "source": "helius_rest"}

    # --- Helper for RPC POST ---
    def _rpc_post(self, method: str, params:Any) -> Dict[str, Any]:
        # if params is None:
        #     params = {}
        # params["api-key"] = self.api_key

        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        try:
            response = self.session.post(self.rpc_url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Helius RPC POST request failed: {e}")
            return {"error": str(e), "source": "helius_rpc"}

    # --- REST Methods (Enhanced API) ---
    def get_enhanced_transactions_by_address(self, address: str, limit: int = 100, before: Optional[str] = None, until: Optional[str] = None, commitment: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"addresses/{address}/transactions"
        params = {"limit": limit}
        if before: params["before"] = before
        if until: params["until"] = until
        if commitment: params["commitment"] = commitment
        return self._rest_get(endpoint, params)

    # --- RPC Methods (Solana JSON-RPC & DAS) ---
    def get_account_info(self, address: str) -> Dict[str, Any]:
        return self._rpc_post("getAccountInfo", [address, {"encoding": "jsonParsed"}])

    def get_token_accounts(self, address: str) -> Dict[str, Any]:
        return self._rpc_post("getTokenAccountsByOwner", [address, {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}, {"encoding": "jsonParsed"}])

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
        return self._rpc_post("getAssetsByOwner", params)

    def get_transaction_history(self, address: str, limit: int = 100) -> Dict[str, Any]:
        return self._rpc_post("getSignaturesForAddress", [address, {"limit": limit}])

    def get_token_metadata(self, mint_address: str) -> Dict[str, Any]:
        return self._rpc_post("getAsset", {"id": mint_address})

    def get_nft_metadata(self, mint_address: str) -> Dict[str, Any]:
        return self._rpc_post("getAsset", {"id": mint_address})

    def get_asset_by_id(self, asset_id: str) -> Dict[str, Any]:
        return self._rpc_post("getAsset", {"id": asset_id})

    def get_assets_by_group(self, group_key: str, group_value: str, page: int = 1) -> Dict[str, Any]:
        return self._rpc_post("getAssetsByGroup", {"groupKey": group_key, "groupValue": group_value, "page": page})

    def get_assets_by_owner(self, owner_address: str, page: int = 1) -> Dict[str, Any]:
        return self._rpc_post("getAssetsByOwner", {"ownerAddress": owner_address, "page": page})

    def get_asset_search(self, query: str, page: int = 1) -> Dict[str, Any]:
        return self._rpc_post("searchAssets", {"query": query, "page": page})

    def get_balance(self, address: str) -> Dict[str, Any]:
        return self._rpc_post("getBalance", [address])

    def get_token_balance(self, address: str, mint_address: str) -> Dict[str, Any]:
        # This requires the token account address, not the mint address
        # You may need to use getTokenAccountsByOwner first to get the token account
        return self._rpc_post("getTokenAccountBalance", [mint_address])

    def get_parsed_transactions(self, transactions: List[str]) -> Dict[str, Any]:
        """Get parsed transaction details for a list of transaction signatures using the REST API."""
        url = f"{self.rest_base_url}/transactions"
        data = {"transactions": transactions}
        try:
            
            response = self.session.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Helius REST API POST request failed: {e}")
            return {"error": str(e), "source": "helius_rest"}

    def get_das_search(self, query: str, limit: int = 100) -> Dict[str, Any]:
        return self._rpc_post("searchAssets", {"query": query, "limit": limit})

   


# Factory function for Helius data source
def create_helius_source(api_key: str, network: str = "mainnet-beta") -> HeliusDataSource:
    """Create a Helius data source instance."""
    return HeliusDataSource(api_key, network) 