"""
Web3 Data Source for LangGraph Assistant
Provides Ethereum blockchain data access via Etherscan API.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from .core import DataSource, DataSourceConfig
import logging

logger = logging.getLogger(__name__)

class Web3DataSource(DataSource):
    """Data source for Ethereum blockchain data via Etherscan API.
    
    This data source provides comprehensive access to Ethereum blockchain data through
    Etherscan's APIs. It supports transaction history, token transfers, gas prices,
    and contract interactions.
    
    Key Features:
    - Transaction history and details
    - Token transfer tracking
    - Gas price monitoring
    - Contract interaction data
    - Address balance information
    
    Supported Networks:
    - Ethereum Mainnet (default)
    - Polygon (via PolygonScan)
    - BSC (via BSCScan)
    - Arbitrum (via Arbiscan)
    
    API Documentation: https://docs.etherscan.io/
    """
    
    def __init__(self, api_key: str, network: str = "ethereum"):
        base_url = self._get_base_url(network)
        config = DataSourceConfig(
            name=f"web3_{network}",
            rest_url=base_url,
            params={"apikey": api_key},
            headers={"Content-Type": "application/json"}
        )
        super().__init__(config)
        self.network = network
        self.api_key = api_key
    
    def health_check(self) -> bool:
        """Check if the Etherscan API is accessible."""
        try:
            response = self.session.get(f"{self.config.rest_url}/api?module=proxy&action=eth_blockNumber&apikey={self.api_key}", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            return False
    
    def _get_base_url(self, network: str) -> str:
        """Get the appropriate base URL for the network."""
        urls = {
            "ethereum": "https://api.etherscan.io",
            "polygon": "https://api.polygonscan.com",
            "bsc": "https://api.bscscan.com",
            "arbitrum": "https://api.arbiscan.io"
        }
        return urls.get(network, "https://api.etherscan.io")
    
    def get_transaction_history(self, address: str, start_block: int = 0, end_block: int = 99999999) -> Dict[str, Any]:
        """Get comprehensive transaction history for an Ethereum address.
        
        Args:
            address (str): Ethereum wallet address (0x format)
            start_block (int): Starting block number (default: 0)
            end_block (int): Ending block number (default: 99999999)
            
        Returns:
            Dict containing transaction history with:
            - Transaction hashes and block numbers
            - From/to addresses and values
            - Gas used and gas price
            - Transaction status and confirmations
            - Timestamp and nonce information
            - Input data and contract interactions
        """
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": "desc"
        }
        return self.get_data("api", params)
    
    def get_token_transfers(self, address: str, contract_address: Optional[str] = None) -> Dict[str, Any]:
        """Get token transfer history for an Ethereum address.
        
        Args:
            address (str): Ethereum wallet address (0x format)
            contract_address (str, optional): Specific token contract address to filter by
            
        Returns:
            Dict containing token transfer history with:
            - Token contract addresses and names
            - Transfer amounts and decimals
            - From/to addresses
            - Transaction hashes and block numbers
            - Gas used and timestamps
            - Token symbol and total supply
        """
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "sort": "desc"
        }
        if contract_address:
            params["contractaddress"] = contract_address
        return self.get_data("api", params)
    
    def get_gas_price(self) -> Dict[str, Any]:
        """Get current gas price estimates for Ethereum network.
        
        Returns:
            Dict containing gas price information with:
            - Safe low gas price (Gwei)
            - Standard gas price (Gwei)
            - Fast gas price (Gwei)
            - Fastest gas price (Gwei)
            - Base fee and priority fee estimates
            - Gas price recommendations
        """
        params = {
            "module": "gastracker",
            "action": "gasoracle"
        }
        return self.get_data("api", params)
    
    def get_contract_abi(self, contract_address: str) -> Dict[str, Any]:
        """Get contract ABI for a verified smart contract.
        
        Args:
            contract_address (str): Smart contract address (0x format)
            
        Returns:
            Dict containing contract information with:
            - Contract ABI (Application Binary Interface)
            - Contract source code
            - Compiler version and settings
            - Contract name and optimization
            - Constructor arguments
            - Verification status
        """
        params = {
            "module": "contract",
            "action": "getabi",
            "address": contract_address
        }
        return self.get_data("api", params)
    
    def get_contract_source(self, contract_address: str) -> Dict[str, Any]:
        """Get verified contract source code and metadata.
        
        Args:
            contract_address (str): Smart contract address (0x format)
            
        Returns:
            Dict containing contract source information with:
            - Contract source code
            - Compiler version and settings
            - Contract name and optimization
            - Constructor arguments
            - Library dependencies
            - Verification details
        """
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": contract_address
        }
        return self.get_data("api", params)
    
    def get_balance(self, address: str) -> Dict[str, Any]:
        """Get ETH balance for an Ethereum address.
        
        Args:
            address (str): Ethereum wallet address (0x format)
            
        Returns:
            Dict containing balance information with:
            - ETH balance in Wei
            - ETH balance in Ether
            - Account status and transaction count
            - Last updated block information
        """
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest"
        }
        return self.get_data("api", params)
    
    def get_token_balance(self, contract_address: str, address: str) -> Dict[str, Any]:
        """Get specific token balance for an Ethereum address.
        
        Args:
            contract_address (str): Token contract address (0x format)
            address (str): Ethereum wallet address (0x format)
            
        Returns:
            Dict containing token balance information with:
            - Token balance in raw units
            - Token balance with decimals
            - Token contract information
            - Account ownership details
            - Token metadata (if available)
        """
        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": contract_address,
            "address": address,
            "tag": "latest"
        }
        return self.get_data("api", params)
    
    def get_block_by_number(self, block_number: int) -> Dict[str, Any]:
        """Get detailed information about a specific block.
        
        Args:
            block_number (int): Block number to retrieve
            
        Returns:
            Dict containing block information with:
            - Block hash and parent hash
            - Block timestamp and miner address
            - Gas limit and gas used
            - Transaction count and list
            - Block difficulty and nonce
            - Base fee and extra data
        """
        params = {
            "module": "proxy",
            "action": "eth_getBlockByNumber",
            "tag": hex(block_number),
            "boolean": "true"
        }
        return self.get_data("api", params)
    
    def get_transaction_by_hash(self, tx_hash: str) -> Dict[str, Any]:
        """Get detailed information about a specific transaction.
        
        Args:
            tx_hash (str): Transaction hash (0x format)
            
        Returns:
            Dict containing transaction information with:
            - Transaction hash and block information
            - From/to addresses and value
            - Gas used and gas price
            - Input data and nonce
            - Transaction status and confirmations
            - Receipt information
        """
        params = {
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": tx_hash
        }
        return self.get_data("api", params)

# Factory function for Web3 data source
def create_web3_source(api_key: str, network: str = "ethereum") -> Web3DataSource:
    """Create a Web3 data source instance.
    
    Args:
        api_key (str): Etherscan API key
        network (str): Blockchain network (ethereum, polygon, bsc, arbitrum)
        
    Returns:
        Web3DataSource: Configured Web3 data source instance
    """
    return Web3DataSource(api_key, network) 