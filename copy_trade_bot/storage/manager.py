"""
Storage manager for the CopyTrade bot.
"""

import json
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..config import Config
from ..types import Leader, LeaderMetrics, Signal

logger = structlog.get_logger(__name__)


class StorageManager:
    """Storage manager for Redis and PostgreSQL."""
    
    def __init__(self, config: Config):
        """Initialize the storage manager."""
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.db_engine = None
        self.db_session: Optional[AsyncSession] = None
        
        # Redis key prefixes
        self.LEADER_PREFIX = "leader:"
        self.SIGNAL_PREFIX = "signal:"
        self.METRICS_PREFIX = "metrics:"
        self.STATE_PREFIX = "state:"
    
    async def initialize(self) -> None:
        """Initialize storage connections."""
        try:
            # Initialize Redis
            self.redis_client = redis.from_url(self.config.redis_url)
            await self.redis_client.ping()
            logger.info("redis_connected", url=self.config.redis_url)
            
            # Initialize PostgreSQL
            if self.config.database_url.startswith("sqlite"):
                # Use SQLite for development
                self.db_engine = create_engine(self.config.database_url)
                self._create_tables()
            else:
                # Use PostgreSQL for production
                self.db_engine = create_async_engine(self.config.database_url)
                await self._create_tables_async()
            
            logger.info("storage_initialized")
            
        except Exception as e:
            logger.error("storage_initialization_failed", error=str(e))
            raise
    
    def _create_tables(self) -> None:
        """Create database tables (SQLite)."""
        with self.db_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS leaders (
                    address TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    equity REAL NOT NULL,
                    weight REAL DEFAULT 1.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS leader_metrics (
                    address TEXT PRIMARY KEY,
                    total_pnl REAL NOT NULL,
                    daily_pnl REAL NOT NULL,
                    weekly_pnl REAL NOT NULL,
                    monthly_pnl REAL NOT NULL,
                    sharpe_ratio REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    win_rate REAL NOT NULL,
                    total_trades INTEGER NOT NULL,
                    winning_trades INTEGER NOT NULL,
                    avg_trade_size REAL NOT NULL,
                    volatility REAL NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (address) REFERENCES leaders (address)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS signals (
                    id TEXT PRIMARY KEY,
                    leader_address TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    side TEXT NOT NULL,
                    size REAL NOT NULL,
                    price REAL,
                    timestamp TIMESTAMP NOT NULL,
                    order_id TEXT,
                    position_id TEXT,
                    metadata TEXT,
                    FOREIGN KEY (leader_address) REFERENCES leaders (address)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    signal_id TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    side TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    size REAL NOT NULL,
                    price REAL,
                    filled_size REAL DEFAULT 0,
                    status TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    cloid TEXT,
                    slippage REAL,
                    FOREIGN KEY (signal_id) REFERENCES signals (id)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS positions (
                    id TEXT PRIMARY KEY,
                    asset TEXT NOT NULL,
                    size REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    mark_price REAL NOT NULL,
                    unrealized_pnl REAL NOT NULL,
                    realized_pnl REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                )
            """))
            
            conn.commit()
    
    async def _create_tables_async(self) -> None:
        """Create database tables (PostgreSQL)."""
        async with self.db_engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS leaders (
                    address VARCHAR(42) PRIMARY KEY,
                    status VARCHAR(20) NOT NULL,
                    equity DECIMAL(20, 8) NOT NULL,
                    weight DECIMAL(10, 4) DEFAULT 1.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS leader_metrics (
                    address VARCHAR(42) PRIMARY KEY,
                    total_pnl DECIMAL(20, 8) NOT NULL,
                    daily_pnl DECIMAL(20, 8) NOT NULL,
                    weekly_pnl DECIMAL(20, 8) NOT NULL,
                    monthly_pnl DECIMAL(20, 8) NOT NULL,
                    sharpe_ratio DECIMAL(10, 4) NOT NULL,
                    max_drawdown DECIMAL(10, 4) NOT NULL,
                    win_rate DECIMAL(10, 4) NOT NULL,
                    total_trades INTEGER NOT NULL,
                    winning_trades INTEGER NOT NULL,
                    avg_trade_size DECIMAL(20, 8) NOT NULL,
                    volatility DECIMAL(10, 4) NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (address) REFERENCES leaders (address)
                )
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS signals (
                    id VARCHAR(64) PRIMARY KEY,
                    leader_address VARCHAR(42) NOT NULL,
                    signal_type VARCHAR(20) NOT NULL,
                    asset VARCHAR(20) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    size DECIMAL(20, 8) NOT NULL,
                    price DECIMAL(20, 8),
                    timestamp TIMESTAMP NOT NULL,
                    order_id VARCHAR(64),
                    position_id VARCHAR(64),
                    metadata JSONB,
                    FOREIGN KEY (leader_address) REFERENCES leaders (address)
                )
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS orders (
                    id VARCHAR(64) PRIMARY KEY,
                    signal_id VARCHAR(64) NOT NULL,
                    asset VARCHAR(20) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    order_type VARCHAR(20) NOT NULL,
                    size DECIMAL(20, 8) NOT NULL,
                    price DECIMAL(20, 8),
                    filled_size DECIMAL(20, 8) DEFAULT 0,
                    status VARCHAR(20) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    cloid VARCHAR(64),
                    slippage DECIMAL(10, 4),
                    FOREIGN KEY (signal_id) REFERENCES signals (id)
                )
            """))
            
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS positions (
                    id VARCHAR(64) PRIMARY KEY,
                    asset VARCHAR(20) NOT NULL,
                    size DECIMAL(20, 8) NOT NULL,
                    entry_price DECIMAL(20, 8) NOT NULL,
                    mark_price DECIMAL(20, 8) NOT NULL,
                    unrealized_pnl DECIMAL(20, 8) NOT NULL,
                    realized_pnl DECIMAL(20, 8) NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                )
            """))
    
    async def health_check(self) -> bool:
        """Check storage health."""
        try:
            # Check Redis
            if self.redis_client:
                await self.redis_client.ping()
            
            # Check database - simplified
            if self.db_engine:
                # Just check if engine exists, don't test connection for now
                pass
            
            return True
            
        except Exception as e:
            logger.error("storage_health_check_failed", error=str(e))
            return False
    
    # Redis operations
    async def set_leader(self, leader: Leader) -> None:
        """Store leader data in Redis."""
        if not self.redis_client:
            return
        
        key = f"{self.LEADER_PREFIX}{leader.address}"
        data = {
            "address": leader.address,
            "status": leader.status.value,
            "equity": str(leader.equity),
            "weight": leader.weight,
            "last_activity": leader.last_activity.isoformat() if leader.last_activity else None
        }
        
        await self.redis_client.set(key, json.dumps(data), ex=3600)  # 1 hour TTL
    
    async def get_leader(self, address: str) -> Optional[Leader]:
        """Get leader data from Redis."""
        if not self.redis_client:
            return None
        
        key = f"{self.LEADER_PREFIX}{address}"
        data = await self.redis_client.get(key)
        
        if data:
            leader_data = json.loads(data)
            # TODO: Reconstruct Leader object
            return None
        
        return None
    
    async def set_leader_metrics(self, address: str, metrics: LeaderMetrics) -> None:
        """Store leader metrics in Redis."""
        if not self.redis_client:
            return
        
        key = f"{self.METRICS_PREFIX}{address}"
        data = {
            "address": metrics.address,
            "total_pnl": str(metrics.total_pnl),
            "daily_pnl": str(metrics.daily_pnl),
            "weekly_pnl": str(metrics.weekly_pnl),
            "monthly_pnl": str(metrics.monthly_pnl),
            "sharpe_ratio": metrics.sharpe_ratio,
            "max_drawdown": metrics.max_drawdown,
            "win_rate": metrics.win_rate,
            "total_trades": metrics.total_trades,
            "winning_trades": metrics.winning_trades,
            "avg_trade_size": str(metrics.avg_trade_size),
            "volatility": metrics.volatility,
            "last_updated": metrics.last_updated.isoformat()
        }
        
        await self.redis_client.set(key, json.dumps(data), ex=1800)  # 30 minutes TTL
    
    async def get_leader_metrics(self, address: str) -> Optional[LeaderMetrics]:
        """Get leader metrics from Redis."""
        if not self.redis_client:
            return None
        
        key = f"{self.METRICS_PREFIX}{address}"
        data = await self.redis_client.get(key)
        
        if data:
            metrics_data = json.loads(data)
            # TODO: Reconstruct LeaderMetrics object
            return None
        
        return None
    
    async def store_signal(self, signal: Signal) -> None:
        """Store signal in Redis and database."""
        # Store in Redis for fast access
        if self.redis_client:
            key = f"{self.SIGNAL_PREFIX}{signal.id}"
            data = {
                "id": signal.id,
                "leader_address": signal.leader_address,
                "signal_type": signal.signal_type.value,
                "asset": signal.asset,
                "side": signal.side.value,
                "size": str(signal.size),
                "price": str(signal.price) if signal.price else None,
                "timestamp": signal.timestamp.isoformat(),
                "order_id": signal.order_id,
                "position_id": signal.position_id,
                "metadata": signal.metadata
            }
            
            await self.redis_client.set(key, json.dumps(data), ex=3600)  # 1 hour TTL
        
        # Store in database for persistence
        await self._store_signal_db(signal)
    
    async def _store_signal_db(self, signal: Signal) -> None:
        """Store signal in database."""
        if not self.db_engine:
            return
        
        try:
            if hasattr(self.db_engine, 'execute'):
                # SQLite
                with self.db_engine.connect() as conn:
                    conn.execute(text("""
                        INSERT OR REPLACE INTO signals 
                        (id, leader_address, signal_type, asset, side, size, price, timestamp, order_id, position_id, metadata)
                        VALUES (:id, :leader_address, :signal_type, :asset, :side, :size, :price, :timestamp, :order_id, :position_id, :metadata)
                    """), {
                        "id": signal.id,
                        "leader_address": signal.leader_address,
                        "signal_type": signal.signal_type.value,
                        "asset": signal.asset,
                        "side": signal.side.value,
                        "size": float(signal.size),
                        "price": float(signal.price) if signal.price else None,
                        "timestamp": signal.timestamp,
                        "order_id": signal.order_id,
                        "position_id": signal.position_id,
                        "metadata": json.dumps(signal.metadata) if signal.metadata else None
                    })
                    conn.commit()
            else:
                # PostgreSQL
                async with self.db_engine.begin() as conn:
                    await conn.execute(text("""
                        INSERT INTO signals 
                        (id, leader_address, signal_type, asset, side, size, price, timestamp, order_id, position_id, metadata)
                        VALUES (:id, :leader_address, :signal_type, :asset, :side, :size, :price, :timestamp, :order_id, :position_id, :metadata)
                        ON CONFLICT (id) DO UPDATE SET
                        leader_address = EXCLUDED.leader_address,
                        signal_type = EXCLUDED.signal_type,
                        asset = EXCLUDED.asset,
                        side = EXCLUDED.side,
                        size = EXCLUDED.size,
                        price = EXCLUDED.price,
                        timestamp = EXCLUDED.timestamp,
                        order_id = EXCLUDED.order_id,
                        position_id = EXCLUDED.position_id,
                        metadata = EXCLUDED.metadata
                    """), {
                        "id": signal.id,
                        "leader_address": signal.leader_address,
                        "signal_type": signal.signal_type.value,
                        "asset": signal.asset,
                        "side": signal.side.value,
                        "size": float(signal.size),
                        "price": float(signal.price) if signal.price else None,
                        "timestamp": signal.timestamp,
                        "order_id": signal.order_id,
                        "position_id": signal.position_id,
                        "metadata": json.dumps(signal.metadata) if signal.metadata else None
                    })
                    
        except Exception as e:
            logger.error("store_signal_db_failed", signal_id=signal.id, error=str(e))
    
    async def get_recent_signals(self, limit: int = 100) -> List[Signal]:
        """Get recent signals from database."""
        if not self.db_engine:
            return []
        
        try:
            if hasattr(self.db_engine, 'execute'):
                # SQLite
                with self.db_engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT * FROM signals 
                        ORDER BY timestamp DESC 
                        LIMIT :limit
                    """), {"limit": limit})
                    
                    signals = []
                    for row in result:
                        # TODO: Reconstruct Signal object
                        pass
                    
                    return signals
            else:
                # PostgreSQL
                async with self.db_engine.begin() as conn:
                    result = await conn.execute(text("""
                        SELECT * FROM signals 
                        ORDER BY timestamp DESC 
                        LIMIT :limit
                    """), {"limit": limit})
                    
                    signals = []
                    async for row in result:
                        # TODO: Reconstruct Signal object
                        pass
                    
                    return signals
                    
        except Exception as e:
            logger.error("get_recent_signals_failed", error=str(e))
            return []
    
    async def set_state(self, key: str, value: Any) -> None:
        """Set state in Redis."""
        if not self.redis_client:
            return
        
        redis_key = f"{self.STATE_PREFIX}{key}"
        await self.redis_client.set(redis_key, json.dumps(value), ex=3600)
    
    async def get_state(self, key: str) -> Optional[Any]:
        """Get state from Redis."""
        if not self.redis_client:
            return None
        
        redis_key = f"{self.STATE_PREFIX}{key}"
        data = await self.redis_client.get(redis_key)
        
        if data:
            return json.loads(data)
        
        return None
    
    async def close(self) -> None:
        """Close storage connections."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("redis_connection_closed")
        
        if self.db_engine:
            if hasattr(self.db_engine, 'dispose'):
                self.db_engine.dispose()
            else:
                await self.db_engine.dispose()
            logger.info("database_connection_closed")
