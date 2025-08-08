"""
Main data client for the CopyTrade bot.
"""

import asyncio
from typing import Any, Dict, List, Optional

import structlog
from hyperliquid.info import Info

from ..config import Config
from ..types import Order, Position, Trade
from ..utils.retry import retry_on_api_error
from .local_node import LocalNodeClient
from .public_api import PublicAPIClient

logger = structlog.get_logger(__name__)


class DataClient:
    """Main data client that manages connections to local node and public API."""
    
    def __init__(self, config: Config):
        """Initialize the data client."""
        self.config = config
        self.local_client: Optional[LocalNodeClient] = None
        self.public_client: Optional[PublicAPIClient] = None
        self.hyperliquid_info: Optional[Info] = None
        
        # Initialize clients
        self._setup_clients()
    
    def _setup_clients(self) -> None:
        """Setup local and public API clients."""
        try:
            # Setup local node client
            self.local_client = LocalNodeClient(self.config.node_info_url)
            logger.info("local_node_client_initialized", url=self.config.node_info_url)
        except Exception as e:
            logger.warning("local_node_client_failed", error=str(e))
            self.local_client = None
        
        # Setup public API client as fallback
        self.public_client = PublicAPIClient(self.config.get_hyperliquid_api_url())
        logger.info("public_api_client_initialized", url=self.config.get_hyperliquid_api_url())
        
        # Setup Hyperliquid SDK Info client
        self.hyperliquid_info = Info(
            base_url=self.config.get_hyperliquid_api_url(),
            skip_ws=True
        )
        logger.info("hyperliquid_info_initialized")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all data sources."""
        health = {
            "local_node": False,
            "public_api": False,
            "hyperliquid_sdk": False
        }
        
        # Check local node
        if self.local_client:
            try:
                await self.local_client.health_check()
                health["local_node"] = True
            except Exception as e:
                logger.warning("local_node_health_check_failed", error=str(e))
        
        # Check public API
        if self.public_client:
            try:
                await self.public_client.health_check()
                health["public_api"] = True
            except Exception as e:
                logger.warning("public_api_health_check_failed", error=str(e))
        
        # Check Hyperliquid SDK
        if self.hyperliquid_info:
            try:
                # Try to get basic info
                self.hyperliquid_info.meta()
                health["hyperliquid_sdk"] = True
            except Exception as e:
                logger.warning("hyperliquid_sdk_health_check_failed", error=str(e))
        
        return health
    
    @retry_on_api_error()
    async def get_user_state(self, address: str) -> Dict[str, Any]:
        """Get user state from the best available source."""
        # Try local node first
        if self.local_client:
            try:
                return await self.local_client.get_user_state(address)
            except Exception as e:
                logger.warning("local_node_user_state_failed", error=str(e))
        
        # Fallback to public API
        if self.public_client:
            return await self.public_client.get_user_state(address)
        
        raise Exception("No data source available")
    
    @retry_on_api_error()
    async def get_open_orders(self, address: str) -> List[Dict[str, Any]]:
        """Get open orders from the best available source."""
        # Try local node first
        if self.local_client:
            try:
                return await self.local_client.get_open_orders(address)
            except Exception as e:
                logger.warning("local_node_open_orders_failed", error=str(e))
        
        # Fallback to public API
        if self.public_client:
            return await self.public_client.get_open_orders(address)
        
        raise Exception("No data source available")
    
    @retry_on_api_error()
    async def get_frontend_open_orders(self, address: str) -> List[Dict[str, Any]]:
        """Get frontend open orders from the best available source."""
        # Try local node first
        if self.local_client:
            try:
                return await self.local_client.get_frontend_open_orders(address)
            except Exception as e:
                logger.warning("local_node_frontend_open_orders_failed", error=str(e))
        
        # Fallback to public API
        if self.public_client:
            return await self.public_client.get_frontend_open_orders(address)
        
        raise Exception("No data source available")
    
    @retry_on_api_error()
    async def get_user_fills(self, address: str, start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get user fills from the best available source."""
        # Try local node first
        if self.local_client:
            try:
                return await self.local_client.get_user_fills(address, start_time, end_time)
            except Exception as e:
                logger.warning("local_node_user_fills_failed", error=str(e))
        
        # Fallback to public API
        if self.public_client:
            return await self.public_client.get_user_fills(address, start_time, end_time)
        
        raise Exception("No data source available")
    
    @retry_on_api_error()
    async def get_clearinghouse_state(self) -> Dict[str, Any]:
        """Get clearinghouse state from the best available source."""
        # Try local node first
        if self.local_client:
            try:
                return await self.local_client.get_clearinghouse_state()
            except Exception as e:
                logger.warning("local_node_clearinghouse_state_failed", error=str(e))
        
        # Fallback to public API
        if self.public_client:
            return await self.public_client.get_clearinghouse_state()
        
        raise Exception("No data source available")
    
    @retry_on_api_error()
    async def get_all_mids(self) -> Dict[str, str]:
        """Get all mid prices."""
        if self.hyperliquid_info:
            return self.hyperliquid_info.all_mids()
        
        # Fallback to public API
        if self.public_client:
            return await self.public_client.get_all_mids()
        
        raise Exception("No data source available")
    
    @retry_on_api_error()
    async def get_l2_snapshot(self, asset: str) -> Dict[str, Any]:
        """Get L2 order book snapshot."""
        if self.hyperliquid_info:
            return self.hyperliquid_info.l2_snapshot(asset)
        
        # Fallback to public API
        if self.public_client:
            return await self.public_client.get_l2_snapshot(asset)
        
        raise Exception("No data source available")
    
    @retry_on_api_error()
    async def get_meta(self) -> Dict[str, Any]:
        """Get exchange metadata."""
        if self.hyperliquid_info:
            return self.hyperliquid_info.meta()
        
        # Fallback to public API
        if self.public_client:
            return await self.public_client.get_meta()
        
        raise Exception("No data source available")
    
    async def get_leader_data(self, leader_address: str) -> Dict[str, Any]:
        """Get comprehensive data for a leader."""
        try:
            # Get user state
            user_state = await self.get_user_state(leader_address)
            
            # Get open orders
            open_orders = await self.get_open_orders(leader_address)
            
            # Get recent fills (last 24 hours)
            end_time = int(asyncio.get_event_loop().time() * 1000)
            start_time = end_time - (24 * 60 * 60 * 1000)  # 24 hours ago
            fills = await self.get_user_fills(leader_address, start_time, end_time)
            
            return {
                "user_state": user_state,
                "open_orders": open_orders,
                "fills": fills,
                "timestamp": end_time
            }
        except Exception as e:
            logger.error("get_leader_data_failed", leader=leader_address, error=str(e))
            raise
    
    async def get_multiple_leaders_data(self, leader_addresses: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get data for multiple leaders concurrently."""
        tasks = []
        for address in leader_addresses:
            task = asyncio.create_task(self.get_leader_data(address))
            tasks.append((address, task))
        
        results = {}
        for address, task in tasks:
            try:
                results[address] = await task
            except Exception as e:
                logger.error("leader_data_failed", leader=address, error=str(e))
                # Continue with other leaders
        
        return results
    
    def get_best_data_source(self) -> str:
        """Get the best available data source."""
        if self.local_client:
            return "local_node"
        elif self.public_client:
            return "public_api"
        else:
            return "none"
    
    async def close(self) -> None:
        """Close all connections."""
        if self.local_client:
            await self.local_client.close()
        
        if self.public_client:
            await self.public_client.close()
        
        if self.hyperliquid_info:
            self.hyperliquid_info.disconnect_websocket()
        
        logger.info("data_client_closed")
