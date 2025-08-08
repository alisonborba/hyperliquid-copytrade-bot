"""
Hyperliquid CopyTrade Bot

Advanced CopyTrade bot for Hyperliquid with real-time leader tracking,
risk management, and low-latency execution.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .config import Config
from .main import CopyTradeBot

__all__ = ["CopyTradeBot", "Config"]
