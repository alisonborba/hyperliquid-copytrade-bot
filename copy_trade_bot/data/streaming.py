"""
Data streaming module for the CopyTrade bot.
"""

import asyncio
import json
from typing import Any, Callable, Dict, Optional

import structlog
import websockets

logger = structlog.get_logger(__name__)


class DataStreamer:
    """WebSocket data streamer for real-time updates."""
    
    def __init__(self, url: str, on_message: Optional[Callable[[Dict[str, Any]], None]] = None):
        """Initialize the data streamer."""
        self.url = url
        self.on_message = on_message
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.running = False
    
    async def connect(self) -> None:
        """Connect to the WebSocket endpoint."""
        try:
            self.websocket = await websockets.connect(self.url)
            logger.info("websocket_connected", url=self.url)
        except Exception as e:
            logger.error("websocket_connection_failed", url=self.url, error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from the WebSocket endpoint."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            logger.info("websocket_disconnected")
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message through the WebSocket."""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error("websocket_send_failed", error=str(e))
                raise
    
    async def receive_messages(self) -> None:
        """Receive and process messages from the WebSocket."""
        if not self.websocket:
            raise RuntimeError("WebSocket not connected")
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    if self.on_message:
                        self.on_message(data)
                    else:
                        logger.debug("websocket_message_received", data=data)
                except json.JSONDecodeError as e:
                    logger.error("websocket_invalid_json", error=str(e), message=message)
                except Exception as e:
                    logger.error("websocket_message_processing_failed", error=str(e))
        except websockets.exceptions.ConnectionClosed:
            logger.info("websocket_connection_closed")
        except Exception as e:
            logger.error("websocket_receive_failed", error=str(e))
            raise
    
    async def start(self) -> None:
        """Start the data streamer."""
        self.running = True
        await self.connect()
        
        while self.running:
            try:
                await self.receive_messages()
            except Exception as e:
                logger.error("websocket_stream_failed", error=str(e))
                if self.running:
                    await asyncio.sleep(5)  # Wait before reconnecting
                    try:
                        await self.connect()
                    except Exception as reconnect_error:
                        logger.error("websocket_reconnect_failed", error=str(reconnect_error))
                        await asyncio.sleep(30)  # Wait longer before next attempt
    
    async def stop(self) -> None:
        """Stop the data streamer."""
        self.running = False
        await self.disconnect()
        logger.info("websocket_streamer_stopped")


class HyperliquidStreamer(DataStreamer):
    """Specialized streamer for Hyperliquid WebSocket API."""
    
    def __init__(self, base_url: str, on_message: Optional[Callable[[Dict[str, Any]], None]] = None):
        """Initialize the Hyperliquid streamer."""
        ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
        super().__init__(f"{ws_url}/ws", on_message)
    
    async def subscribe_to_user_updates(self, user_address: str) -> None:
        """Subscribe to user updates."""
        subscription = {
            "type": "subscribe",
            "channel": "user",
            "user": user_address
        }
        await self.send_message(subscription)
        logger.info("subscribed_to_user_updates", user=user_address)
    
    async def subscribe_to_orderbook(self, asset: str) -> None:
        """Subscribe to orderbook updates."""
        subscription = {
            "type": "subscribe",
            "channel": "orderbook",
            "asset": asset
        }
        await self.send_message(subscription)
        logger.info("subscribed_to_orderbook", asset=asset)
    
    async def subscribe_to_trades(self, asset: str) -> None:
        """Subscribe to trade updates."""
        subscription = {
            "type": "subscribe",
            "channel": "trades",
            "asset": asset
        }
        await self.send_message(subscription)
        logger.info("subscribed_to_trades", asset=asset)
