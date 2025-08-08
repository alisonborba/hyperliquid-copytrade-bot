"""
Local node client for accessing --serve-info endpoints.
"""

import json
from typing import Any, Dict, List, Optional

import aiohttp
import structlog

logger = structlog.get_logger(__name__)


class LocalNodeClient:
    """Client for accessing local node --serve-info endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:3001/info"):
        """Initialize the local node client."""
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=5.0)  # 5 second timeout
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created."""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
    
    async def _make_request(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the local node."""
        await self._ensure_session()
        
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        
        try:
            if data:
                async with self.session.post(url, json=data) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error("local_node_request_failed", endpoint=endpoint, error=str(e))
            raise
        except Exception as e:
            logger.error("local_node_unexpected_error", endpoint=endpoint, error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """Check if local node is healthy."""
        try:
            # Try to get exchange status
            await self._make_request("exchangeStatus")
            return True
        except Exception as e:
            logger.warning("local_node_health_check_failed", error=str(e))
            return False
    
    async def get_user_state(self, address: str) -> Dict[str, Any]:
        """Get user state from local node."""
        data = {"type": "userState", "user": address}
        return await self._make_request("", data)
    
    async def get_open_orders(self, address: str) -> List[Dict[str, Any]]:
        """Get open orders from local node."""
        data = {"type": "openOrders", "user": address}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_frontend_open_orders(self, address: str) -> List[Dict[str, Any]]:
        """Get frontend open orders from local node."""
        data = {"type": "frontendOpenOrders", "user": address}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_user_fills(self, address: str, start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get user fills from local node."""
        data = {"type": "userFills", "user": address}
        if start_time is not None:
            data["startTime"] = start_time
        if end_time is not None:
            data["endTime"] = end_time
        
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_clearinghouse_state(self) -> Dict[str, Any]:
        """Get clearinghouse state from local node."""
        data = {"type": "clearinghouseState"}
        return await self._make_request("", data)
    
    async def get_spot_clearinghouse_state(self) -> Dict[str, Any]:
        """Get spot clearinghouse state from local node."""
        data = {"type": "spotClearinghouseState"}
        return await self._make_request("", data)
    
    async def get_exchange_status(self) -> Dict[str, Any]:
        """Get exchange status from local node."""
        data = {"type": "exchangeStatus"}
        return await self._make_request("", data)
    
    async def get_liquidatable(self) -> List[Dict[str, Any]]:
        """Get liquidatable positions from local node."""
        data = {"type": "liquidatable"}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_active_asset_data(self) -> List[Dict[str, Any]]:
        """Get active asset data from local node."""
        data = {"type": "activeAssetData"}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_max_market_order_ntls(self) -> Dict[str, Any]:
        """Get max market order notional from local node."""
        data = {"type": "maxMarketOrderNtls"}
        return await self._make_request("", data)
    
    async def get_vault_summaries(self) -> List[Dict[str, Any]]:
        """Get vault summaries from local node."""
        data = {"type": "vaultSummaries"}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_user_vault_equities(self) -> List[Dict[str, Any]]:
        """Get user vault equities from local node."""
        data = {"type": "userVaultEquities"}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_leading_vaults(self) -> List[Dict[str, Any]]:
        """Get leading vaults from local node."""
        data = {"type": "leadingVaults"}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_extra_agents(self) -> List[Dict[str, Any]]:
        """Get extra agents from local node."""
        data = {"type": "extraAgents"}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_sub_accounts(self) -> List[Dict[str, Any]]:
        """Get sub accounts from local node."""
        data = {"type": "subAccounts"}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_user_fees(self, address: str) -> Dict[str, Any]:
        """Get user fees from local node."""
        data = {"type": "userFees", "user": address}
        return await self._make_request("", data)
    
    async def get_user_rate_limit(self, address: str) -> Dict[str, Any]:
        """Get user rate limit from local node."""
        data = {"type": "userRateLimit", "user": address}
        return await self._make_request("", data)
    
    async def get_spot_deploy_state(self) -> Dict[str, Any]:
        """Get spot deploy state from local node."""
        data = {"type": "spotDeployState"}
        return await self._make_request("", data)
    
    async def get_perp_deploy_auction_status(self) -> Dict[str, Any]:
        """Get perp deploy auction status from local node."""
        data = {"type": "perpDeployAuctionStatus"}
        return await self._make_request("", data)
    
    async def get_delegations(self, address: str) -> List[Dict[str, Any]]:
        """Get delegations from local node."""
        data = {"type": "delegations", "user": address}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_delegator_summary(self, address: str) -> Dict[str, Any]:
        """Get delegator summary from local node."""
        data = {"type": "delegatorSummary", "user": address}
        return await self._make_request("", data)
    
    async def get_max_builder_fee(self) -> Dict[str, Any]:
        """Get max builder fee from local node."""
        data = {"type": "maxBuilderFee"}
        return await self._make_request("", data)
    
    async def get_user_to_multi_sig_signers(self, address: str) -> Dict[str, Any]:
        """Get user to multi-sig signers from local node."""
        data = {"type": "userToMultiSigSigners", "user": address}
        return await self._make_request("", data)
    
    async def get_user_role(self, address: str) -> Dict[str, Any]:
        """Get user role from local node."""
        data = {"type": "userRole", "user": address}
        return await self._make_request("", data)
    
    async def get_perps_at_open_interest_cap(self) -> List[Dict[str, Any]]:
        """Get perps at open interest cap from local node."""
        data = {"type": "perpsAtOpenInterestCap"}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_validator_l1_votes(self) -> List[Dict[str, Any]]:
        """Get validator L1 votes from local node."""
        data = {"type": "validatorL1Votes"}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_margin_table(self) -> Dict[str, Any]:
        """Get margin table from local node."""
        data = {"type": "marginTable"}
        return await self._make_request("", data)
    
    async def get_perp_dexs(self) -> List[Dict[str, Any]]:
        """Get perp DEXs from local node."""
        data = {"type": "perpDexs"}
        response = await self._make_request("", data)
        return response.get("data", [])
    
    async def get_web_data2(self) -> Dict[str, Any]:
        """Get web data 2 from local node."""
        data = {"type": "webData2"}
        return await self._make_request("", data)
    
    async def get_file_snapshot(self, snapshot_type: str, out_path: str, include_height: bool = False) -> Dict[str, Any]:
        """Get file snapshot from local node."""
        data = {
            "type": "fileSnapshot",
            "request": {"type": snapshot_type},
            "outPath": out_path,
            "includeHeightInOutput": include_height
        }
        return await self._make_request("", data)
    
    async def get_referrer_states_snapshot(self, out_path: str) -> Dict[str, Any]:
        """Get referrer states snapshot."""
        return await self.get_file_snapshot("referrerStates", out_path)
    
    async def get_l4_snapshots(self, out_path: str, include_users: bool = True, include_trigger_orders: bool = True) -> Dict[str, Any]:
        """Get L4 snapshots."""
        data = {
            "type": "fileSnapshot",
            "request": {
                "type": "l4Snapshots",
                "includeUsers": include_users,
                "includeTriggerOrders": include_trigger_orders
            },
            "outPath": out_path,
            "includeHeightInOutput": False
        }
        return await self._make_request("", data)
    
    async def close(self) -> None:
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("local_node_client_closed")
