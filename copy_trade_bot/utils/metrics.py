"""
Prometheus metrics setup for the CopyTrade bot.
"""

import time
from typing import Dict, Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
    start_http_server,
)


class Metrics:
    """Prometheus metrics for the CopyTrade bot."""
    
    def __init__(self, port: int = 8000):
        """Initialize metrics."""
        self.port = port
        
        # Counters
        self.signals_total = Counter(
            "copytrade_signals_total",
            "Total number of signals received",
            ["leader", "asset", "signal_type"]
        )
        
        self.orders_placed_total = Counter(
            "copytrade_orders_placed_total",
            "Total number of orders placed",
            ["asset", "side", "order_type", "status"]
        )
        
        self.orders_filled_total = Counter(
            "copytrade_orders_filled_total",
            "Total number of orders filled",
            ["asset", "side", "order_type"]
        )
        
        self.errors_total = Counter(
            "copytrade_errors_total",
            "Total number of errors",
            ["module", "error_type"]
        )
        
        # Gauges
        self.active_leaders = Gauge(
            "copytrade_active_leaders",
            "Number of active leaders being followed"
        )
        
        self.open_positions = Gauge(
            "copytrade_open_positions",
            "Number of open positions",
            ["asset"]
        )
        
        self.open_orders = Gauge(
            "copytrade_open_orders",
            "Number of open orders",
            ["asset", "side"]
        )
        
        self.total_pnl = Gauge(
            "copytrade_total_pnl",
            "Total PnL in USD"
        )
        
        self.daily_pnl = Gauge(
            "copytrade_daily_pnl",
            "Daily PnL in USD"
        )
        
        self.total_exposure = Gauge(
            "copytrade_total_exposure",
            "Total portfolio exposure in USD"
        )
        
        self.leader_equity = Gauge(
            "copytrade_leader_equity",
            "Leader equity in USD",
            ["leader"]
        )
        
        self.leader_score = Gauge(
            "copytrade_leader_score",
            "Leader performance score",
            ["leader"]
        )
        
        # Histograms
        self.signal_latency = Histogram(
            "copytrade_signal_latency_seconds",
            "Time from signal to execution",
            ["asset", "signal_type"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        )
        
        self.order_slippage = Histogram(
            "copytrade_order_slippage_bps",
            "Order slippage in basis points",
            ["asset", "side"],
            buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000]
        )
        
        self.api_latency = Histogram(
            "copytrade_api_latency_seconds",
            "API request latency",
            ["endpoint", "method"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        )
        
        # Summaries
        self.leader_performance = Summary(
            "copytrade_leader_performance",
            "Leader performance metrics",
            ["leader", "metric"]
        )
        
        self.risk_metrics = Summary(
            "copytrade_risk_metrics",
            "Risk management metrics",
            ["metric"]
        )
        
        # Start metrics server
        try:
            start_http_server(port)
        except OSError:
            # Port might already be in use, ignore
            pass
    
    def record_signal(self, leader: str, asset: str, signal_type: str) -> None:
        """Record a signal received."""
        self.signals_total.labels(leader=leader, asset=asset, signal_type=signal_type).inc()
    
    def record_order_placed(self, asset: str, side: str, order_type: str, status: str) -> None:
        """Record an order placed."""
        self.orders_placed_total.labels(
            asset=asset, side=side, order_type=order_type, status=status
        ).inc()
    
    def record_order_filled(self, asset: str, side: str, order_type: str) -> None:
        """Record an order filled."""
        self.orders_filled_total.labels(asset=asset, side=side, order_type=order_type).inc()
    
    def record_error(self, module: str, error_type: str) -> None:
        """Record an error."""
        self.errors_total.labels(module=module, error_type=error_type).inc()
    
    def set_active_leaders(self, count: int) -> None:
        """Set the number of active leaders."""
        self.active_leaders.set(count)
    
    def set_open_positions(self, asset: str, count: int) -> None:
        """Set the number of open positions for an asset."""
        self.open_positions.labels(asset=asset).set(count)
    
    def set_open_orders(self, asset: str, side: str, count: int) -> None:
        """Set the number of open orders for an asset and side."""
        self.open_orders.labels(asset=asset, side=side).set(count)
    
    def set_total_pnl(self, pnl: float) -> None:
        """Set the total PnL."""
        self.total_pnl.set(pnl)
    
    def set_daily_pnl(self, pnl: float) -> None:
        """Set the daily PnL."""
        self.daily_pnl.set(pnl)
    
    def set_total_exposure(self, exposure: float) -> None:
        """Set the total portfolio exposure."""
        self.total_exposure.set(exposure)
    
    def set_leader_equity(self, leader: str, equity: float) -> None:
        """Set the equity for a leader."""
        self.leader_equity.labels(leader=leader).set(equity)
    
    def set_leader_score(self, leader: str, score: float) -> None:
        """Set the performance score for a leader."""
        self.leader_score.labels(leader=leader).set(score)
    
    def observe_signal_latency(self, asset: str, signal_type: str, latency: float) -> None:
        """Observe signal to execution latency."""
        self.signal_latency.labels(asset=asset, signal_type=signal_type).observe(latency)
    
    def observe_order_slippage(self, asset: str, side: str, slippage_bps: float) -> None:
        """Observe order slippage."""
        self.order_slippage.labels(asset=asset, side=side).observe(slippage_bps)
    
    def observe_api_latency(self, endpoint: str, method: str, latency: float) -> None:
        """Observe API request latency."""
        self.api_latency.labels(endpoint=endpoint, method=method).observe(latency)
    
    def observe_leader_performance(self, leader: str, metric: str, value: float) -> None:
        """Observe leader performance metric."""
        self.leader_performance.labels(leader=leader, metric=metric).observe(value)
    
    def observe_risk_metric(self, metric: str, value: float) -> None:
        """Observe risk management metric."""
        self.risk_metrics.labels(metric=metric).observe(value)
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return generate_latest().decode('utf-8')


# Global metrics instance
_metrics: Optional[Metrics] = None


def setup_metrics(port: int = 8000) -> Metrics:
    """Setup and return the global metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = Metrics(port)
    return _metrics


def get_metrics() -> Metrics:
    """Get the global metrics instance."""
    if _metrics is None:
        raise RuntimeError("Metrics not initialized. Call setup_metrics() first.")
    return _metrics


class MetricsTimer:
    """Context manager for timing operations and recording metrics."""
    
    def __init__(self, metrics: Metrics, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Initialize the timer."""
        self.metrics = metrics
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record metric."""
        if self.start_time is not None:
            duration = time.time() - self.start_time
            
            if self.metric_name == "signal_latency":
                self.metrics.observe_signal_latency(
                    self.labels.get("asset", "unknown"),
                    self.labels.get("signal_type", "unknown"),
                    duration
                )
            elif self.metric_name == "api_latency":
                self.metrics.observe_api_latency(
                    self.labels.get("endpoint", "unknown"),
                    self.labels.get("method", "unknown"),
                    duration
                )
            elif self.metric_name == "order_slippage":
                self.metrics.observe_order_slippage(
                    self.labels.get("asset", "unknown"),
                    self.labels.get("side", "unknown"),
                    duration
                )
