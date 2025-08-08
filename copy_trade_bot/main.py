"""
Main CopyTrade bot implementation.
"""

import asyncio
import signal
import sys
from typing import Dict, List, Optional

import click
import structlog
from rich.console import Console
from rich.table import Table

from .config import Config
from .data import DataClient
from .execution import ExecutionEngine
from .leaders import LeaderManager
from .risk import RiskManager
from .signals import SignalProcessor
from .storage import StorageManager
from .types import BotState, HealthCheck
from .utils.logging import setup_logging
from .utils.metrics import setup_metrics
from .utils.time import get_current_datetime

console = Console()
logger = structlog.get_logger(__name__)


class CopyTradeBot:
    """Main CopyTrade bot class."""
    
    def __init__(self, config: Config):
        """Initialize the CopyTrade bot."""
        self.config = config
        self.running = False
        self.start_time = get_current_datetime()
        
        # Setup logging and metrics
        setup_logging(config.log_level, config.log_format)
        self.metrics = setup_metrics(config.metrics_port)
        
        # Initialize components
        self.data_client = DataClient(config)
        self.storage = StorageManager(config)
        self.leader_manager = LeaderManager(config, self.data_client, self.storage)
        self.risk_manager = RiskManager(config, self.storage)
        self.signal_processor = SignalProcessor(config, self.storage)
        self.execution_engine = ExecutionEngine(config, self.data_client, self.storage)
        
        # State tracking
        self.total_signals = 0
        self.total_orders = 0
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        
        logger.info("copytrade_bot_initialized", config=config.model_dump())
    
    async def start(self) -> None:
        """Start the CopyTrade bot."""
        try:
            logger.info("starting_copytrade_bot")
            
            # Initialize storage
            await self.storage.initialize()
            
            # Health check
            health = await self.health_check()
            if not health.status == "healthy":
                logger.error("health_check_failed", health=health.model_dump())
                return
            
            # Start components
            await self.leader_manager.start()
            await self.risk_manager.start()
            await self.signal_processor.start()
            await self.execution_engine.start()
            
            self.running = True
            logger.info("copytrade_bot_started")
            
            # Main event loop
            await self._main_loop()
            
        except Exception as e:
            logger.error("bot_start_failed", error=str(e), exc_info=True)
            raise
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the CopyTrade bot."""
        if not self.running:
            return
        
        logger.info("stopping_copytrade_bot")
        self.running = False
        
        try:
            # Stop components
            await self.leader_manager.stop()
            await self.risk_manager.stop()
            await self.signal_processor.stop()
            await self.execution_engine.stop()
            
            # Close connections
            await self.data_client.close()
            await self.storage.close()
            
            logger.info("copytrade_bot_stopped")
            
        except Exception as e:
            logger.error("bot_stop_failed", error=str(e))
    
    async def _main_loop(self) -> None:
        """Main event loop."""
        while self.running:
            try:
                # Update leader rankings
                await self.leader_manager.update_rankings()
                
                # Process signals
                signals = await self.signal_processor.get_signals()
                for signal in signals:
                    await self._process_signal(signal)
                
                # Update metrics
                await self._update_metrics()
                
                # Check risk limits
                if not await self.risk_manager.check_limits():
                    logger.warning("risk_limits_exceeded")
                    break
                
                # Sleep
                await asyncio.sleep(1)  # 1 second loop
                
            except Exception as e:
                logger.error("main_loop_error", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_signal(self, signal) -> None:
        """Process a trading signal."""
        try:
            # Validate signal
            if not self.signal_processor.validate_signal(signal):
                logger.warning("invalid_signal", signal_id=signal.id)
                return
            
            # Check risk limits
            if not await self.risk_manager.can_execute_signal(signal):
                logger.warning("signal_blocked_by_risk", signal_id=signal.id)
                return
            
            # Execute signal
            result = await self.execution_engine.execute_signal(signal)
            
            if result.success:
                self.total_signals += 1
                self.total_orders += 1
                logger.info("signal_executed", signal_id=signal.id, result=result)
            else:
                logger.error("signal_execution_failed", signal_id=signal.id, error=result.error)
            
        except Exception as e:
            logger.error("signal_processing_failed", signal_id=signal.id, error=str(e))
    
    async def _update_metrics(self) -> None:
        """Update metrics."""
        try:
            # Get current state
            state = await self.get_state()
            
            # Update Prometheus metrics
            self.metrics.set_total_pnl(state.total_pnl)
            self.metrics.set_daily_pnl(state.daily_pnl)
            self.metrics.set_active_leaders(state.active_leaders)
            
            # Update risk metrics
            risk_metrics = await self.risk_manager.get_metrics()
            self.metrics.set_total_exposure(risk_metrics.total_exposure)
            
        except Exception as e:
            logger.error("metrics_update_failed", error=str(e))
    
    async def health_check(self) -> HealthCheck:
        """Perform health check."""
        errors = []
        
        # Check data sources
        data_health = await self.data_client.health_check()
        if not any(data_health.values()):
            errors.append("No data sources available")
        
        # Check storage
        try:
            await self.storage.health_check()
        except Exception as e:
            errors.append(f"Storage error: {str(e)}")
        
        # Check risk manager
        try:
            await self.risk_manager.health_check()
        except Exception as e:
            errors.append(f"Risk manager error: {str(e)}")
        
        # Calculate uptime
        uptime = (get_current_datetime() - self.start_time).total_seconds()
        
        return HealthCheck(
            status="healthy" if not errors else "unhealthy",
            timestamp=get_current_datetime(),
            uptime_seconds=uptime,
            version="0.1.0",
            node_connected=data_health.get("local_node", False),
            database_connected=data_health.get("public_api", False),
            redis_connected=True,  # TODO: Check Redis
            active_leaders=len(await self.leader_manager.get_active_leaders()),
            total_signals=self.total_signals,
            total_orders=self.total_orders,
            errors=errors
        )
    
    async def get_state(self) -> BotState:
        """Get current bot state."""
        risk_metrics = await self.risk_manager.get_metrics()
        
        return BotState(
            is_running=self.running,
            total_signals=self.total_signals,
            total_orders=self.total_orders,
            total_pnl=self.total_pnl,
            daily_pnl=self.daily_pnl,
            active_leaders=len(await self.leader_manager.get_active_leaders()),
            risk_metrics=risk_metrics,
            last_updated=get_current_datetime()
        )
    
    def print_status(self) -> None:
        """Print current bot status."""
        table = Table(title="CopyTrade Bot Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Status", "Running" if self.running else "Stopped")
        table.add_row("Total Signals", str(self.total_signals))
        table.add_row("Total Orders", str(self.total_orders))
        table.add_row("Total PnL", f"${self.total_pnl:.2f}")
        table.add_row("Daily PnL", f"${self.daily_pnl:.2f}")
        table.add_row("Uptime", f"{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        console.print(table)


@click.command()
@click.option("--config", "-c", help="Configuration file path")
@click.option("--dry-run", is_flag=True, help="Run in dry-run mode")
@click.option("--leaders", help="Comma-separated list of leader addresses")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(config: Optional[str], dry_run: bool, leaders: Optional[str], verbose: bool) -> None:
    """CopyTrade bot for Hyperliquid."""
    try:
        # Load configuration
        if config:
            # TODO: Load from YAML/JSON file
            pass
        
        cfg = Config()
        
        # Override with command line options
        if dry_run:
            cfg.dry_run = True
        
        if leaders:
            cfg.allowed_leaders = [addr.strip() for addr in leaders.split(",")]
        
        if verbose:
            cfg.log_level = "DEBUG"
        
        # Create and run bot
        bot = CopyTradeBot(cfg)
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info("received_shutdown_signal", signal=signum)
            asyncio.create_task(bot.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run bot
        asyncio.run(bot.start())
        
    except KeyboardInterrupt:
        logger.info("shutdown_requested")
    except Exception as e:
        logger.error("main_error", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
