"""
Public API client for Hyperliquid as fallback.
"""

import json
from typing import Any, Dict, List, Optional

import aiohttp
import structlog

logger = structlog.get_logger(__name__)


class PublicAPIClient:
    """Client for Hyperliquid public API endpoints."""
    
    def __init__(self, base_url: str):
        """Initialize the public API client."""
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=10.0)  # 10 second timeout
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created."""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
    
    async def _make_request(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the public API."""
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
            logger.error("public_api_request_failed", endpoint=endpoint, error=str(e))
            raise
        except Exception as e:
            logger.error("public_api_unexpected_error", endpoint=endpoint, error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """Check if public API is healthy."""
        try:
            # Try to get meta data
            await self._make_request("info", {"type": "meta"})
            return True
        except Exception as e:
            logger.warning("public_api_health_check_failed", error=str(e))
            return False
    
    async def get_user_state(self, address: str) -> Dict[str, Any]:
        """Get user state from public API."""
        data = {"type": "userState", "user": address}
        return await self._make_request("info", data)
    
    async def get_open_orders(self, address: str) -> List[Dict[str, Any]]:
        """Get open orders from public API."""
        data = {"type": "openOrders", "user": address}
        response = await self._make_request("info", data)
        return response.get("data", [])
    
    async def get_frontend_open_orders(self, address: str) -> List[Dict[str, Any]]:
        """Get frontend open orders from public API."""
        data = {"type": "frontendOpenOrders", "user": address}
        response = await self._make_request("info", data)
        return response.get("data", [])
    
    async def get_user_fills(self, address: str, start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get user fills from public API."""
        data = {"type": "userFills", "user": address}
        if start_time is not None:
            data["startTime"] = start_time
        if end_time is not None:
            data["endTime"] = end_time
        
        response = await self._make_request("info", data)
        return response.get("data", [])
    
    async def get_clearinghouse_state(self) -> Dict[str, Any]:
        """Get clearinghouse state from public API."""
        data = {"type": "clearinghouseState"}
        return await self._make_request("info", data)
    
    async def get_all_mids(self) -> Dict[str, str]:
        """Get all mid prices from public API."""
        data = {"type": "allMids"}
        response = await self._make_request("info", data)
        return response.get("data", {})
    
    async def get_l2_snapshot(self, asset: str) -> Dict[str, Any]:
        """Get L2 order book snapshot from public API."""
        data = {"type": "l2Book", "coin": asset}
        response = await self._make_request("info", data)
        return response.get("data", {})
    
    async def get_meta(self) -> Dict[str, Any]:
        """Get exchange metadata from public API."""
        data = {"type": "meta"}
        return await self._make_request("info", data)
    
    async def get_spot_meta(self) -> Dict[str, Any]:
        """Get spot metadata from public API."""
        data = {"type": "spotMeta"}
        return await self._make_request("info", data)
    
    async def get_funding_history(self, asset: str, start_time: int, end_time: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get funding history from public API."""
        data = {"type": "fundingHistory", "coin": asset, "startTime": start_time}
        if end_time is not None:
            data["endTime"] = end_time
        
        response = await self._make_request("info", data)
        return response.get("data", [])
    
    async def get_user_funding_history(self, address: str, start_time: int, end_time: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get user funding history from public API."""
        data = {"type": "userFundingHistory", "user": address, "startTime": start_time}
        if end_time is not None:
            data["endTime"] = end_time
        
        response = await self._make_request("info", data)
        return response.get("data", [])
    
    async def get_candles(self, asset: str, interval: str, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """Get candle data from public API."""
        data = {
            "type": "candlesV2",
            "coin": asset,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time
        }
        
        response = await self._make_request("info", data)
        return response.get("data", [])
    
    async def get_user_fees(self, address: str) -> Dict[str, Any]:
        """Get user fees from public API."""
        data = {"type": "userFees", "user": address}
        return await self._make_request("info", data)
    
    async def get_user_staking_summary(self, address: str) -> Dict[str, Any]:
        """Get user staking summary from public API."""
        data = {"type": "userStakingSummary", "user": address}
        return await self._make_request("info", data)
    
    async def get_user_staking_delegations(self, address: str) -> List[Dict[str, Any]]:
        """Get user staking delegations from public API."""
        data = {"type": "userStakingDelegations", "user": address}
        response = await self._make_request("info", data)
        return response.get("data", [])
    
    async def get_user_staking_rewards(self, address: str) -> List[Dict[str, Any]]:
        """Get user staking rewards from public API."""
        data = {"type": "userStakingRewards", "user": address}
        response = await self._make_request("info", data)
        return response.get("data", [])
    
    async def get_delegations(self, address: str) -> List[Dict[str, Any]]:
        """Get delegations from public API."""
        data = {"type": "delegations", "user": address}
        response = await self._make_request("info", data)
        return response.get("data", [])
    
    async def get_delegator_summary(self, address: str) -> Dict[str, Any]:
        """Get delegator summary from public API."""
        data = {"type": "delegatorSummary", "user": address}
        return await self._make_request("info", data)
    
    async def get_validator_summaries(self) -> List[Dict[str, Any]]:
        """Get validator summaries from public API."""
        data = {"type": "validatorSummaries"}
        response = await self._make_request("info", data)
        return response.get("data", [])
    
    async def get_perp_dexs(self) -> List[Dict[str, Any]]:
        """Get perp DEXs from public API."""
        data = {"type": "perpDexs"}
        response = await self._make_request("info", data)
        return response.get("data", [])
    
    async def get_web_data2(self) -> Dict[str, Any]:
        """Get web data 2 from public API."""
        data = {"type": "webData2"}
        return await self._make_request("info", data)
    
    async def close(self) -> None:
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("public_api_client_closed")
