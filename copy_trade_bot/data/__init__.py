"""
Data ingestion and management for the CopyTrade bot.
"""

from .client import DataClient
from .local_node import LocalNodeClient
from .public_api import PublicAPIClient
from .streaming import DataStreamer

__all__ = [
    "DataClient",
    "LocalNodeClient", 
    "PublicAPIClient",
    "DataStreamer",
]
