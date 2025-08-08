"""
Type definitions for the CopyTrade bot.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enumeration."""
    LIMIT = "limit"
    MARKET = "market"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class SignalType(str, Enum):
    """Signal type enumeration."""
    NEW_ORDER = "new_order"
    MODIFY_ORDER = "modify_order"
    CANCEL_ORDER = "cancel_order"
    POSITION_UPDATE = "position_update"


class LeaderStatus(str, Enum):
    """Leader status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    SUSPENDED = "suspended"


@dataclass
class PriceLevel:
    """Price level in order book."""
    price: Decimal
    size: Decimal


@dataclass
class OrderBook:
    """Order book snapshot."""
    asset: str
    timestamp: datetime
    bids: List[PriceLevel]
    asks: List[PriceLevel]
    last_price: Optional[Decimal] = None


@dataclass
class Trade:
    """Trade information."""
    id: str
    asset: str
    side: OrderSide
    size: Decimal
    price: Decimal
    timestamp: datetime
    maker: str
    taker: str


@dataclass
class Position:
    """Position information."""
    asset: str
    size: Decimal
    entry_price: Decimal
    mark_price: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    timestamp: datetime


@dataclass
class Order:
    """Order information."""
    id: str
    asset: str
    side: OrderSide
    order_type: OrderType
    size: Decimal
    price: Optional[Decimal]
    filled_size: Decimal
    status: str
    timestamp: datetime
    cloid: Optional[str] = None


@dataclass
class Signal:
    """Trading signal from a leader."""
    id: str
    leader_address: str
    signal_type: SignalType
    asset: str
    side: OrderSide
    size: Decimal
    price: Optional[Decimal]
    timestamp: datetime
    order_id: Optional[str] = None
    position_id: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class LeaderMetrics:
    """Performance metrics for a leader."""
    address: str
    total_pnl: Decimal
    daily_pnl: Decimal
    weekly_pnl: Decimal
    monthly_pnl: Decimal
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    winning_trades: int
    avg_trade_size: Decimal
    volatility: float
    last_updated: datetime


@dataclass
class Leader:
    """Leader information."""
    address: str
    status: LeaderStatus
    metrics: LeaderMetrics
    equity: Decimal
    positions: List[Position]
    open_orders: List[Order]
    weight: float = 1.0
    last_activity: Optional[datetime] = None


@dataclass
class ExecutionResult:
    """Result of order execution."""
    success: bool
    order_id: Optional[str] = None
    filled_size: Optional[Decimal] = None
    filled_price: Optional[Decimal] = None
    slippage: Optional[float] = None
    error: Optional[str] = None
    timestamp: datetime = None


@dataclass
class RiskMetrics:
    """Risk metrics for the bot."""
    total_exposure: Decimal
    daily_pnl: Decimal
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    avg_slippage: float
    last_updated: datetime


class LeaderRanking(BaseModel):
    """Leader ranking information."""
    address: str
    score: float
    rank: int
    metrics: LeaderMetrics
    weight: float = 1.0
    
    class Config:
        arbitrary_types_allowed = True


class BotState(BaseModel):
    """Current state of the bot."""
    is_running: bool
    total_signals: int
    total_orders: int
    total_pnl: Decimal
    daily_pnl: Decimal
    active_leaders: int
    risk_metrics: RiskMetrics
    last_updated: datetime
    
    class Config:
        arbitrary_types_allowed = True


class ConfigUpdate(BaseModel):
    """Configuration update request."""
    max_daily_loss: Optional[float] = None
    max_position_size: Optional[float] = None
    max_total_exposure: Optional[float] = None
    default_slippage_bps: Optional[int] = None
    follow_window_seconds: Optional[int] = None
    max_leaders_to_follow: Optional[int] = None
    banned_leaders: Optional[List[str]] = None
    allowed_leaders: Optional[List[str]] = None
    leader_weights: Optional[Dict[str, float]] = None


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    uptime_seconds: float
    version: str
    node_connected: bool
    database_connected: bool
    redis_connected: bool
    active_leaders: int
    total_signals: int
    total_orders: int
    errors: List[str] = []


class MetricsSnapshot(BaseModel):
    """Metrics snapshot for monitoring."""
    timestamp: datetime
    signals_per_second: float
    orders_per_second: float
    avg_latency_ms: float
    avg_slippage_bps: float
    total_pnl: Decimal
    daily_pnl: Decimal
    active_positions: int
    open_orders: int
    leader_count: int
    error_rate: float
    
    class Config:
        arbitrary_types_allowed = True
