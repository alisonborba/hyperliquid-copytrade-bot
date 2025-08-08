"""
Structured logging setup for the CopyTrade bot.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    include_timestamp: bool = True,
    include_module: bool = True,
) -> None:
    """
    Setup structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json or text)
        include_timestamp: Whether to include timestamp in logs
        include_module: Whether to include module name in logs
    """
    # Configure structlog
    processors = []
    
    if include_timestamp:
        processors.append(structlog.stdlib.filter_by_level)
        processors.append(structlog.stdlib.add_logger_name)
        processors.append(structlog.stdlib.add_log_level)
        processors.append(structlog.stdlib.PositionalArgumentsFormatter())
        processors.append(structlog.processors.TimeStamper(fmt="iso"))
    else:
        processors.extend([
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
        ])
    
    if include_module:
        processors.append(structlog.processors.StackInfoRenderer())
    
    if log_format == "json":
        processors.append(structlog.processors.format_exc_info)
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually module name)
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


def log_signal(logger: structlog.stdlib.BoundLogger, signal: Any, **kwargs: Any) -> None:
    """
    Log a trading signal.
    
    Args:
        logger: Logger instance
        signal: Signal object
        **kwargs: Additional context
    """
    logger.info(
        "signal_received",
        signal_id=signal.id,
        leader=signal.leader_address,
        asset=signal.asset,
        side=signal.side.value,
        size=str(signal.size),
        price=str(signal.price) if signal.price else None,
        signal_type=signal.signal_type.value,
        **kwargs,
    )


def log_order(logger: structlog.stdlib.BoundLogger, order: Any, **kwargs: Any) -> None:
    """
    Log an order execution.
    
    Args:
        logger: Logger instance
        order: Order object
        **kwargs: Additional context
    """
    logger.info(
        "order_executed",
        order_id=order.id,
        asset=order.asset,
        side=order.side.value,
        size=str(order.size),
        price=str(order.price) if order.price else None,
        order_type=order.order_type.value,
        status=order.status,
        **kwargs,
    )


def log_leader_update(logger: structlog.stdlib.BoundLogger, leader: Any, **kwargs: Any) -> None:
    """
    Log a leader update.
    
    Args:
        logger: Logger instance
        leader: Leader object
        **kwargs: Additional context
    """
    logger.info(
        "leader_updated",
        leader_address=leader.address,
        status=leader.status.value,
        equity=str(leader.equity),
        total_pnl=str(leader.metrics.total_pnl),
        sharpe_ratio=leader.metrics.sharpe_ratio,
        win_rate=leader.metrics.win_rate,
        **kwargs,
    )


def log_error(logger: structlog.stdlib.BoundLogger, error: Exception, context: Dict[str, Any]) -> None:
    """
    Log an error with context.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context about the error
    """
    logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **context,
        exc_info=True,
    )


def log_metrics(logger: structlog.stdlib.BoundLogger, metrics: Any, **kwargs: Any) -> None:
    """
    Log performance metrics.
    
    Args:
        logger: Logger instance
        metrics: Metrics object
        **kwargs: Additional context
    """
    logger.info(
        "metrics_update",
        total_pnl=str(metrics.total_pnl),
        daily_pnl=str(metrics.daily_pnl),
        sharpe_ratio=metrics.sharpe_ratio,
        win_rate=metrics.win_rate,
        total_trades=metrics.total_trades,
        avg_slippage=metrics.avg_slippage,
        **kwargs,
    )
