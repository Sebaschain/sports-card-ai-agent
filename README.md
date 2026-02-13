# 🏀 Sports Card AI Agent

An intelligent multi-agent system for analyzing and trading sports cards using AI, built with LangChain, LangGraph, and the Model Context Protocol (MCP).

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-37-green.svg)](#-running-tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Overview

This project implements a sophisticated AI-powered system for sports card investment analysis. It combines multiple specialized AI agents that work together to provide comprehensive market research, player performance analysis, and trading recommendations.

## ✨ Key Features

| Feature | Status | Description |
|---------|--------|-------------|
| Multi-Agent System | ✅ | Coordinated AI agents using LangGraph |
| Market Research | ✅ | Real-time eBay integration with circuit breaker |
| Player Analysis | ✅ | Performance evaluation from real sports APIs |
| Trading Strategy | ✅ | Intelligent buy/sell/hold recommendations |
| MCP Server | ⚠️ | Standardized protocol for tool exposure |
| Web Interface | ✅ | Interactive Streamlit dashboard |
| Claude Desktop | ⚠️ | Integration available via MCP |
| **Unit Tests** | ✅ | 37+ tests with pytest |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                 USER INTERFACE                      │
│           Streamlit App / Claude Desktop            │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                  MCP SERVER                         │
│         (Model Context Protocol)                    │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              SUPERVISOR AGENT                       │
│            (LangGraph Orchestration)                │
└──────────┬──────────────┬──────────────┬───────────┘
           │              │              │
    ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼─────────┐
    │  Market    │ │  Player    │ │  Trading     │
    │  Research  │ │  Analysis  │ │  Strategy    │
    │  Agent ✓   │ │  Agent     │ │  Agent ✓     │
    └────────────┘ └────────────┘ └──────────────┘
           │              │              │
    ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼─────────┐
    │  eBay API  │ │ NBA/NHL/   │ │ Configurable │
    │  + Cache   │ │ MLB/NFL    │ │ Thresholds   │
    └────────────┘ └────────────┘ └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- UV package manager
- eBay Developer Account (optional)
- NBA/NHL/MLB/NFL API keys (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sports-card-ai-agent.git
cd sports-card-ai-agent

# Install UV (if not already installed)
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

```bash
# Web interface
streamlit run app.py

# Run tests
python -m pytest tests/unit/ -v

# Run linting
ruff check src/ tests/
ruff format src/ tests/
```

## 📁 Project Structure

```
sports-card-ai-agent/
├── src/
│   ├── agents/
│   │   ├── market_research_agent.py    # ✅ Market analysis + circuit breaker
│   │   ├── player_analysis_agent.py    # Player performance
│   │   ├── trading_strategy_agent.py   # ✅ Configurable trading signals
│   │   └── supervisor_agent.py         # LangGraph orchestration
│   ├── tools/
│   │   ├── ebay_tool.py                # eBay API integration
│   │   ├── nba_stats_tool.py           # NBA API
│   │   ├── nhl_stats_tool.py           # NHL API
│   │   ├── mlb_stats_tool.py           # MLB API
│   │   ├── nfl_stats_tool.py           # NFL API
│   │   └── soccer_stats_tool.py        # Soccer API
│   ├── mcp/
│   │   ├── server.py                   # MCP server
│   │   └── tools.py                    # MCP tool definitions
│   ├── models/
│   │   └── card.py                     # Pydantic data models
│   └── utils/
│       ├── config.py                   # Configuration management
│       ├── exceptions.py               # ✅ Custom exceptions
│       ├── logging_config.py           # ✅ JSON structured logging
│       └── stats_cache.py              # Cache for API responses
├── tests/
│   ├── conftest.py                     # Shared pytest fixtures
│   └── unit/
│       ├── agents/
│       │   ├── test_supervisor_agent.py       # 5 tests
│       │   ├── test_market_research_agent.py # 7 tests
│       │   └── test_trading_strategy_agent.py # 15 tests
│       └── models/
│           └── test_card.py            # 15 tests
├── data/
│   ├── raw/                            # Raw data storage
│   └── processed/                      # Processed data
├── pyproject.toml                      # ✅ Unified dependencies
├── .pre-commit-config.yaml             # Pre-commit hooks
└── README.md                           # This file
```

## 🧪 Running Tests

```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run with coverage
python -m pytest tests/unit/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/unit/agents/test_trading_strategy_agent.py -v

# Run tests matching pattern
python -m pytest -k "test_generate_strategy" -v
```

### Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| SupervisorAgent | 5 | ✅ Passing |
| MarketResearchAgent | 7 | ✅ Passing |
| TradingStrategyAgent | 15 | ✅ Passing |
| Models (Card, Player) | 15 | ✅ Passing |
| **Total** | **37+** | ✅ |

## 🔧 Configuration

### Trading Strategy Thresholds

The trading strategy agent is now configurable:

```python
from src.agents.trading_strategy_agent import TradingStrategyAgent

# Create agent with custom thresholds
agent = TradingStrategyAgent(
    buy_threshold=85,      # Score for BUY signal
    hold_threshold=70,    # Score for HOLD signal
    entry_discount=0.95,  # Entry price discount
    target_multiplier=1.25, # Target sell multiplier
    stop_loss_discount=0.85,
)

# Or update dynamically
agent.set_thresholds(buy_threshold=88)
```

### Circuit Breaker Settings

```python
from src.agents.market_research_agent import CircuitBreaker

# Configure circuit breaker
breaker = CircuitBreaker(
    failure_threshold=5,   # Failures before opening
    recovery_timeout=60.0, # Seconds before retry
)
```

## 📊 Error Handling

The system now includes robust error handling:

```python
from src.utils.exceptions import (
    MarketDataError,
    APITemporarilyUnavailableError,
    RateLimitExceededError,
    AuthenticationError,
    ValidationError,
    ConfigurationError,
)
```

### Logging

Structured JSON logging is now available:

```json
{
  "timestamp": "2025-02-09T19:00:00Z",
  "level": "INFO",
  "logger": "MarketResearchAgent",
  "message": "Researching market for card: LeBron James 2003 Topps",
  "context_id": "2025-02-09T19:00:00Z_12345",
  "search_query": "LeBron James 2003 Topps"
}
```

## 🤝 Contributing

1. Install development dependencies: `uv sync --dev`
2. Install pre-commit hooks: `pre-commit install`
3. Run tests: `python -m pytest tests/unit/ -v`
4. Run linting: `ruff check src/ tests/`
5. Format code: `ruff format src/ tests/`

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://python.langchain.com/) for AI orchestration
- [LangGraph](https://langchain.dev/langgraph/) for agent workflows
- [eBay API](https://developer.ebay.com/) for market data
- [Streamlit](https://streamlit.io/) for the web interface
