"""
Tests for configuration module.
"""

import os
import pytest
from unittest.mock import patch

from copy_trade_bot.config import Config


class TestConfig:
    """Test cases for Config class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.hyperliquid_chain == "Mainnet"
        assert config.node_info_url == "http://localhost:3001/info"
        assert config.database_url == "sqlite:///copytrade.db"
        assert config.redis_url == "redis://localhost:6379/0"
        assert config.max_daily_loss == 0.05
        assert config.max_position_size == 0.1
        assert config.max_total_exposure == 0.5
        assert config.default_slippage_bps == 50
        assert config.follow_window_seconds == 5
        assert config.leader_update_interval == 300
        assert config.min_leader_equity == 10000
        assert config.max_leaders_to_follow == 10
        assert config.performance_lookback_days == 30
        assert config.dry_run is False
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 1.0
        assert config.log_level == "INFO"
        assert config.log_format == "json"
        assert config.metrics_port == 8000
        assert config.health_check_port == 8001
        assert config.enable_websocket is True
        assert config.websocket_timeout == 30
        assert config.batch_size == 100
        assert config.banned_leaders == []
        assert config.allowed_leaders == []
        assert config.leader_weights == {}
    
    def test_environment_override(self):
        """Test environment variable override."""
        with patch.dict(os.environ, {
            "HYPERLIQUID_CHAIN": "Testnet",
            "MAX_DAILY_LOSS": "0.1",
            "DRY_RUN": "true",
            "LOG_LEVEL": "DEBUG"
        }):
            config = Config()
            
            assert config.hyperliquid_chain == "Testnet"
            assert config.max_daily_loss == 0.1
            assert config.dry_run is True
            assert config.log_level == "DEBUG"
    
    def test_chain_validation(self):
        """Test chain validation."""
        with patch.dict(os.environ, {"HYPERLIQUID_CHAIN": "Invalid"}):
            with pytest.raises(ValueError, match="Chain must be one of"):
                Config()
    
    def test_percentage_validation(self):
        """Test percentage validation."""
        with patch.dict(os.environ, {"MAX_DAILY_LOSS": "1.5"}):
            with pytest.raises(ValueError, match="Percentage must be between 0 and 1"):
                Config()
        
        with patch.dict(os.environ, {"MAX_POSITION_SIZE": "-0.1"}):
            with pytest.raises(ValueError, match="Percentage must be between 0 and 1"):
                Config()
    
    def test_slippage_validation(self):
        """Test slippage validation."""
        with patch.dict(os.environ, {"DEFAULT_SLIPPAGE_BPS": "1500"}):
            with pytest.raises(ValueError, match="Slippage must be between 0 and 1000 bps"):
                Config()
        
        with patch.dict(os.environ, {"DEFAULT_SLIPPAGE_BPS": "-50"}):
            with pytest.raises(ValueError, match="Slippage must be between 0 and 1000 bps"):
                Config()
    
    def test_follow_window_validation(self):
        """Test follow window validation."""
        with patch.dict(os.environ, {"FOLLOW_WINDOW_SECONDS": "0"}):
            with pytest.raises(ValueError, match="Follow window must be between 1 and 60 seconds"):
                Config()
        
        with patch.dict(os.environ, {"FOLLOW_WINDOW_SECONDS": "120"}):
            with pytest.raises(ValueError, match="Follow window must be between 1 and 60 seconds"):
                Config()
    
    def test_leader_update_interval_validation(self):
        """Test leader update interval validation."""
        with patch.dict(os.environ, {"LEADER_UPDATE_INTERVAL": "30"}):
            with pytest.raises(ValueError, match="Leader update interval must be between 60 and 3600 seconds"):
                Config()
        
        with patch.dict(os.environ, {"LEADER_UPDATE_INTERVAL": "7200"}):
            with pytest.raises(ValueError, match="Leader update interval must be between 60 and 3600 seconds"):
                Config()
    
    def test_max_leaders_validation(self):
        """Test max leaders validation."""
        with patch.dict(os.environ, {"MAX_LEADERS_TO_FOLLOW": "0"}):
            with pytest.raises(ValueError, match="Max leaders must be between 1 and 50"):
                Config()
        
        with patch.dict(os.environ, {"MAX_LEADERS_TO_FOLLOW": "100"}):
            with pytest.raises(ValueError, match="Max leaders must be between 1 and 50"):
                Config()
    
    def test_performance_lookback_validation(self):
        """Test performance lookback validation."""
        with patch.dict(os.environ, {"PERFORMANCE_LOOKBACK_DAYS": "0"}):
            with pytest.raises(ValueError, match="Performance lookback must be between 1 and 365 days"):
                Config()
        
        with patch.dict(os.environ, {"PERFORMANCE_LOOKBACK_DAYS": "400"}):
            with pytest.raises(ValueError, match="Performance lookback must be between 1 and 365 days"):
                Config()
    
    def test_log_level_validation(self):
        """Test log level validation."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            with pytest.raises(ValueError, match="Log level must be one of"):
                Config()
    
    def test_log_format_validation(self):
        """Test log format validation."""
        with patch.dict(os.environ, {"LOG_FORMAT": "invalid"}):
            with pytest.raises(ValueError, match="Log format must be one of"):
                Config()
    
    def test_get_hyperliquid_api_url(self):
        """Test get_hyperliquid_api_url method."""
        config = Config()
        
        # Test Mainnet
        assert config.get_hyperliquid_api_url() == "https://api.hyperliquid.xyz"
        
        # Test Testnet
        with patch.dict(os.environ, {"HYPERLIQUID_CHAIN": "Testnet"}):
            config = Config()
            assert config.get_hyperliquid_api_url() == "https://api.hyperliquid-testnet.xyz"
    
    def test_get_node_data_path(self):
        """Test get_node_data_path method."""
        config = Config()
        expected_path = os.path.expanduser("~/hl/data")
        assert config.get_node_data_path() == expected_path
    
    def test_is_testnet(self):
        """Test is_testnet method."""
        config = Config()
        assert config.is_testnet() is False
        
        with patch.dict(os.environ, {"HYPERLIQUID_CHAIN": "Testnet"}):
            config = Config()
            assert config.is_testnet() is True
    
    def test_is_dry_run(self):
        """Test is_dry_run method."""
        config = Config()
        assert config.is_dry_run() is False
        
        with patch.dict(os.environ, {"DRY_RUN": "true"}):
            config = Config()
            assert config.is_dry_run() is True
        
        with patch.dict(os.environ, {"DRY_RUN": "false"}):
            config = Config()
            assert config.is_dry_run() is False
    
    def test_leader_filtering(self):
        """Test leader filtering configuration."""
        with patch.dict(os.environ, {
            "BANNED_LEADERS": "0x123,0x456",
            "ALLOWED_LEADERS": "0x789,0xabc",
            "LEADER_WEIGHTS": '{"0x123": 0.5, "0x456": 0.8}'
        }):
            config = Config()
            
            assert config.banned_leaders == ["0x123", "0x456"]
            assert config.allowed_leaders == ["0x789", "0xabc"]
            assert config.leader_weights == {"0x123": 0.5, "0x456": 0.8}
    
    def test_required_fields(self):
        """Test required fields validation."""
        # Remove required field
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="field required"):
                Config()
    
    def test_config_dict(self):
        """Test config.dict() method."""
        config = Config()
        config_dict = config.dict()
        
        assert isinstance(config_dict, dict)
        assert "hyperliquid_chain" in config_dict
        assert "max_daily_loss" in config_dict
        assert "dry_run" in config_dict
