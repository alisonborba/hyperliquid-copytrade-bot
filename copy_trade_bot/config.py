"""
Configuration management for the CopyTrade bot.
"""

import os
import json
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Main configuration class for the CopyTrade bot."""
    
    # Hyperliquid Configuration
    hyperliquid_chain: str = Field(default="Mainnet", env="HYPERLIQUID_CHAIN")
    hyperliquid_private_key: str = Field(..., env="HYPERLIQUID_PRIVATE_KEY")
    hyperliquid_vault_address: Optional[str] = Field(None, env="HYPERLIQUID_VAULT_ADDRESS")
    
    # Node Configuration
    node_info_url: str = Field(default="http://localhost:3001/info", env="NODE_INFO_URL")
    node_data_path: str = Field(default="~/hl/data", env="NODE_DATA_PATH")
    fallback_to_public_api: bool = Field(default=True, env="FALLBACK_TO_PUBLIC_API")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///copytrade.db", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Risk Management
    max_daily_loss: float = Field(default=0.05, env="MAX_DAILY_LOSS")  # 5% max daily loss
    max_position_size: float = Field(default=0.1, env="MAX_POSITION_SIZE")  # 10% max position size
    max_total_exposure: float = Field(default=0.5, env="MAX_TOTAL_EXPOSURE")  # 50% max total exposure
    default_slippage_bps: int = Field(default=50, env="DEFAULT_SLIPPAGE_BPS")  # 0.5% default slippage
    follow_window_seconds: int = Field(default=5, env="FOLLOW_WINDOW_SECONDS")  # 5 second follow window
    
    # Leader Selection
    leader_update_interval: int = Field(default=300, env="LEADER_UPDATE_INTERVAL")  # 5 minutes
    min_leader_equity: float = Field(default=10000, env="MIN_LEADER_EQUITY")  # $10k minimum equity
    max_leaders_to_follow: int = Field(default=10, env="MAX_LEADERS_TO_FOLLOW")
    performance_lookback_days: int = Field(default=30, env="PERFORMANCE_LOOKBACK_DAYS")
    
    # Execution Settings
    dry_run: bool = Field(default=False, env="DRY_RUN")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay_seconds: float = Field(default=1.0, env="RETRY_DELAY_SECONDS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Monitoring
    metrics_port: int = Field(default=8000, env="METRICS_PORT")
    health_check_port: int = Field(default=8001, env="HEALTH_CHECK_PORT")
    
    # Advanced Settings
    enable_websocket: bool = Field(default=True, env="ENABLE_WEBSOCKET")
    websocket_timeout: int = Field(default=30, env="WEBSOCKET_TIMEOUT")
    batch_size: int = Field(default=100, env="BATCH_SIZE")
    
    # Leader Filtering
    banned_leaders: List[str] = Field(default_factory=list, env="BANNED_LEADERS")
    allowed_leaders: List[str] = Field(default_factory=list, env="ALLOWED_LEADERS")
    leader_weights: dict = Field(default_factory=dict, env="LEADER_WEIGHTS")
    
    @field_validator("hyperliquid_chain")
    @classmethod
    def validate_chain(cls, v: str) -> str:
        """Validate the Hyperliquid chain configuration."""
        valid_chains = ["Mainnet", "Testnet"]
        if v not in valid_chains:
            raise ValueError(f"Chain must be one of {valid_chains}")
        return v
    
    @field_validator("max_daily_loss", "max_position_size", "max_total_exposure")
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Validate percentage values are between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Percentage must be between 0 and 1")
        return v
    
    @field_validator("default_slippage_bps")
    @classmethod
    def validate_slippage(cls, v: int) -> int:
        """Validate slippage is positive and reasonable."""
        if v < 0 or v > 1000:  # Max 10%
            raise ValueError("Slippage must be between 0 and 1000 bps")
        return v
    
    @field_validator("follow_window_seconds")
    @classmethod
    def validate_follow_window(cls, v: int) -> int:
        """Validate follow window is reasonable."""
        if v < 1 or v > 60:
            raise ValueError("Follow window must be between 1 and 60 seconds")
        return v
    
    @field_validator("leader_update_interval")
    @classmethod
    def validate_update_interval(cls, v: int) -> int:
        """Validate leader update interval."""
        if v < 60 or v > 3600:
            raise ValueError("Leader update interval must be between 60 and 3600 seconds")
        return v
    
    @field_validator("max_leaders_to_follow")
    @classmethod
    def validate_max_leaders(cls, v: int) -> int:
        """Validate maximum number of leaders."""
        if v < 1 or v > 50:
            raise ValueError("Max leaders must be between 1 and 50")
        return v
    
    @field_validator("performance_lookback_days")
    @classmethod
    def validate_lookback_days(cls, v: int) -> int:
        """Validate performance lookback period."""
        if v < 1 or v > 365:
            raise ValueError("Performance lookback must be between 1 and 365 days")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        valid_formats = ["json", "text"]
        if v not in valid_formats:
            raise ValueError(f"Log format must be one of {valid_formats}")
        return v
    
    @field_validator("banned_leaders", "allowed_leaders", mode="before")
    @classmethod
    def parse_list_fields(cls, v):
        """Parse list fields from environment variables."""
        if isinstance(v, str):
            if v.strip() == "":
                return []
            return [item.strip() for item in v.split(",") if item.strip()]
        return v or []

    @field_validator("leader_weights", mode="before")
    @classmethod
    def parse_dict_fields(cls, v):
        """Parse dict fields from environment variables."""
        if isinstance(v, str):
            if v.strip() == "":
                return {}
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v or {}
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_hyperliquid_api_url(self) -> str:
        """Get the appropriate Hyperliquid API URL based on chain."""
        if self.hyperliquid_chain == "Testnet":
            return "https://api.hyperliquid-testnet.xyz"
        return "https://api.hyperliquid.xyz"
    
    def get_node_data_path(self) -> str:
        """Expand the node data path."""
        return os.path.expanduser(self.node_data_path)
    
    def is_testnet(self) -> bool:
        """Check if running on testnet."""
        return self.hyperliquid_chain == "Testnet"
    
    def is_dry_run(self) -> bool:
        """Check if running in dry-run mode."""
        return self.dry_run or os.getenv("DRY_RUN", "false").lower() == "true"
