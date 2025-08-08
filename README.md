# Hyperliquid CopyTrade Bot

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/Poetry-1.4+-orange.svg)](https://python-poetry.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Check](https://img.shields.io/badge/type%20check-mypy-blue.svg)](https://mypy-lang.org/)

A high-performance, production-ready copy trading bot for the Hyperliquid decentralized exchange. This project demonstrates advanced Python development practices, real-time data processing, risk management, and automated trading strategies.

## 🚀 Features

### Core Functionality
- **Real-time Leader Tracking**: Dynamic ranking system based on performance metrics
- **Low-latency Signal Processing**: Sub-second response to market opportunities
- **Advanced Risk Management**: Multi-layered risk controls and position sizing
- **Automated Execution**: Smart order routing with slippage protection
- **Comprehensive Monitoring**: Prometheus metrics and structured logging

### Technical Highlights
- **Modular Architecture**: Clean separation of concerns with dependency injection
- **Async/Await**: High-performance concurrent operations
- **Type Safety**: Full type annotations with mypy validation
- **Error Handling**: Robust retry mechanisms and graceful degradation
- **Configuration Management**: Environment-based configuration with validation
- **Data Persistence**: Redis caching + PostgreSQL/SQLite for audit trails

### Risk Management
- Daily loss limits and position size controls
- Dynamic stop-loss and take-profit mechanisms
- Exposure limits per asset and total portfolio
- Cooldown periods after consecutive losses
- Slippage protection and liquidity filters

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Layer    │    │  Signal Layer   │    │ Execution Layer │
│                 │    │                 │    │                 │
│ • Local Node    │───▶│ • Signal Detect │───▶│ • Order Mgmt    │
│ • Public API    │    │ • Validation    │    │ • Risk Checks   │
│ • WebSocket     │    │ • Normalization │    │ • Execution     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Storage Layer  │    │  Leader Layer   │    │ Monitoring      │
│                 │    │                 │    │                 │
│ • Redis Cache   │    │ • Ranking       │    │ • Prometheus    │
│ • PostgreSQL    │    │ • Metrics       │    │ • Structured    │
│ • SQLite        │    │ • Selection     │    │   Logging       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

- **Python 3.9+**: Core language with async/await support
- **Poetry**: Dependency management and packaging
- **Pydantic**: Data validation and settings management
- **SQLAlchemy**: Database ORM and migrations
- **Redis**: High-performance caching and queues
- **aiohttp**: Async HTTP client/server
- **structlog**: Structured logging for observability
- **Prometheus**: Metrics collection and monitoring
- **Hyperliquid SDK**: Official exchange integration

## 📋 Prerequisites

- Python 3.9 or higher
- Poetry (for dependency management)
- Redis server
- PostgreSQL (optional, SQLite for development)
- Hyperliquid account and API keys

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/hyperliquid-copytrade-bot.git
cd hyperliquid-copytrade-bot
poetry install
```

### 2. Configuration

```bash
cp env.example .env
# Edit .env with your configuration
```

Key configuration variables:
```env
HYPERLIQUID_CHAIN=Testnet  # or Mainnet
HYPERLIQUID_PRIVATE_KEY=your_private_key
MAX_DAILY_LOSS=0.05        # 5% max daily loss
MAX_POSITION_SIZE=0.1      # 10% max position size
DRY_RUN=true              # Start in safe mode
```

### 3. Start Services

```bash
# Start Redis (if not running)
redis-server

# Start the bot
poetry run python -m copy_trade_bot.main --dry-run --verbose
```

### 4. Monitor

- **Metrics**: http://localhost:8000/metrics
- **Health Check**: http://localhost:8001/health
- **Logs**: Structured JSON logs in console

## 📊 Leader Ranking Algorithm

The bot uses a sophisticated multi-factor ranking system:

### Performance Metrics (40% weight)
- **7-day rolling return**: Recent performance
- **30-day Sharpe ratio**: Risk-adjusted returns
- **Hit ratio**: Win/loss ratio

### Risk Metrics (30% weight)
- **Maximum drawdown**: Risk exposure
- **Volatility**: Price stability
- **Position concentration**: Diversification

### Consistency Metrics (20% weight)
- **Trade frequency**: Activity level
- **Strategy consistency**: Behavioral patterns

### Size and Activity (10% weight)
- **Account size**: Capital base
- **Recent activity**: Current engagement

## 🔧 Development

### Project Structure

```
copy-trade-bot/
├── copy_trade_bot/           # Main package
│   ├── config.py            # Configuration management
│   ├── main.py              # Application entry point
│   ├── types.py             # Type definitions
│   ├── data/                # Data ingestion layer
│   ├── storage/             # Persistence layer
│   ├── leaders/             # Leader management
│   ├── signals/             # Signal processing
│   ├── risk/                # Risk management
│   ├── execution/           # Order execution
│   └── utils/               # Shared utilities
├── scripts/                 # Automation scripts
├── tests/                   # Test suite
├── docs/                    # Documentation
└── pyproject.toml          # Project configuration
```

### Code Quality

```bash
# Format code
poetry run black .
poetry run isort .

# Type checking
poetry run mypy .

# Linting
poetry run flake8 .

# Security audit
poetry run bandit -r copy_trade_bot/

# Run tests
poetry run pytest
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run all hooks
poetry run pre-commit run --all-files
```

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=copy_trade_bot

# Run specific test categories
poetry run pytest tests/test_config.py
poetry run pytest tests/test_data/
```

## 📈 Monitoring and Observability

### Metrics (Prometheus)

- **Trading Metrics**: Signals processed, orders executed, PnL
- **Performance Metrics**: Latency, throughput, error rates
- **Risk Metrics**: Exposure levels, drawdown, Sharpe ratio
- **System Metrics**: Memory usage, CPU, database connections

### Logging

Structured JSON logs for easy parsing and analysis:

```json
{
  "event": "signal_executed",
  "signal_id": "abc123",
  "leader_address": "0x...",
  "asset": "BTC",
  "side": "buy",
  "size": "0.1",
  "price": "50000",
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "info"
}
```

## 🔒 Security Considerations

- **Private Keys**: Never commit private keys to version control
- **Environment Variables**: Use `.env` files for sensitive configuration
- **Network Security**: All API communications use HTTPS
- **Rate Limiting**: Respect exchange rate limits
- **Dry Run Mode**: Always test in dry-run mode first

## 🚨 Risk Disclaimer

**This software is for educational and research purposes only. Trading cryptocurrencies involves substantial risk of loss. Use at your own risk and never trade with money you cannot afford to lose.**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive tests
- Update documentation for new features
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Hyperliquid](https://hyperliquid.xyz/) for the exchange platform
- [Hyperliquid Python SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk) for API integration
- The open-source community for various libraries and tools

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/hyperliquid-copytrade-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/hyperliquid-copytrade-bot/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/hyperliquid-copytrade-bot/wiki)

---

**Built with ❤️ for the DeFi community**
