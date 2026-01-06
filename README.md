🏀 Sports Card AI Agent
An intelligent multi-agent system for analyzing and trading sports cards using AI, built with LangChain, LangGraph, and the Model Context Protocol (MCP).
Show Image
Show Image
Show Image
🎯 Overview
This project implements a sophisticated AI-powered system for sports card investment analysis. It combines multiple specialized AI agents that work together to provide comprehensive market research, player performance analysis, and trading recommendations.
Key Features

🤖 Multi-Agent System: Coordinated AI agents using LangGraph
📊 Market Research: Real-time eBay integration for price analysis
🏀 Player Analysis: Performance evaluation and risk assessment
📈 Trading Strategy: Intelligent buy/sell/hold recommendations
🔌 MCP Server: Standardized protocol for tool exposure
🌐 Web Interface: Interactive Streamlit dashboard
💻 Claude Desktop Integration: Direct access from Claude AI

🏗️ Architecture
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
    │  Agent     │ │  Agent     │ │  Agent       │
    └────────────┘ └────────────┘ └──────────────┘
🚀 Quick Start
Prerequisites

Python 3.13+
UV package manager
eBay Developer Account (optional)
OpenAI API Key (optional)

Installation

Clone the repository

bashgit clone https://github.com/yourusername/sports-card-ai-agent.git
cd sports-card-ai-agent

Install UV (if not already installed)

powershell# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

Install dependencies

bashuv sync

Configure environment variables

bashcp .env.example .env
# Edit .env with your API keys

Run the application

bash# Web interface
streamlit run app.py

# Or test the multi-agent system
python test_agents_simple.py
📁 Project Structure
sports-card-ai-agent/
├── src/
│   ├── agents/
│   │   ├── market_research_agent.py    # Market analysis
│   │   ├── player_analysis_agent.py    # Player performance
│   │   ├── trading_strategy_agent.py   # Trading signals
│   │   └── supervisor_agent.py         # LangGraph orchestration
│   ├── tools/
│   │   └── ebay_tool.py                # eBay API integration
│   ├── mcp/
│   │   ├── server.py                   # MCP server
│   │   └── tools.py                    # MCP tool definitions
│   ├── models/
│   │   └── card.py                     # Pydantic data models
│   └── utils/
│       └── config.py                   # Configuration management
├── data/
│   ├── raw/                            # Raw data storage
│   └── processed/                      # Processed data
├── tests/
│   └── test_*.py                       # Test files
├── app.py                              # Streamlit web app
├── run_mcp_server.py                   # MCP server launcher
├── pyproject.toml                      # Project dependencies
└── README.md                           # This file
🤖 Multi-Agent System
Market Research Agent

Searches eBay for card listings
Analyzes price trends and market liquidity
Compares sold vs active listings
Provides market insights

Player Analysis Agent

Evaluates player performance
Assesses career trajectory and trends
Identifies risk factors (injuries, age, etc.)
Generates future outlook predictions

Trading Strategy Agent

Combines market and player data
Generates BUY/SELL/HOLD signals
Calculates entry/exit price targets
Evaluates risk/reward ratios
Provides actionable recommendations

Supervisor Agent

Coordinates workflow between agents
Manages state and data flow
Generates consolidated reports
Uses LangGraph for orchestration

🔌 MCP Server
The Model Context Protocol (MCP) server exposes four main tools:
Available Tools

search_sports_cards

Search for sports cards on eBay
Filter by price, sport, and condition
View sold or active listings


analyze_card_investment

Analyze a specific card for investment potential
Get AI-powered BUY/SELL/HOLD signals
Receive detailed reasoning and confidence levels


get_player_card_recommendations

Get card recommendations for a specific player
Filter by budget constraints
Ranked by value score


compare_card_prices

Compare prices between sold and active listings
Understand market dynamics
Identify pricing trends



Connecting to Claude Desktop

Create/edit ~/.config/Claude/claude_desktop_config.json:

json{
  "mcpServers": {
    "sports-card-agent": {
      "command": "/path/to/your/.venv/bin/python",
      "args": ["/path/to/your/run_mcp_server.py"]
    }
  }
}

Restart Claude Desktop
Ask Claude: "What MCP tools do you have available?"

🌐 Web Interface
The Streamlit app provides three main tabs:
🔍 eBay Search

Search cards with advanced filters
View real-time listings with images
See prices, conditions, and seller info

📊 Card Analysis

Input card details
Get AI-powered investment analysis
View interactive price charts
Receive trading recommendations

📈 Dashboard

Market statistics (coming soon)
Portfolio tracking (coming soon)
Historical performance (coming soon)

📊 Data Models
The system uses Pydantic models for type-safe data handling:

Player: Player information and metadata
Card: Sports card details and specifications
PricePoint: Individual price observation
PriceHistory: Historical price data
PlayerStats: Performance statistics
TradingRecommendation: AI-generated recommendations

🧪 Testing
bash# Test simple agents
python test_agents_simple.py

# Test MCP tools
python test_mcp_client.py

# Test eBay integration
python test_ebay.py

# Run all tests
pytest tests/
🛠️ Configuration
Environment Variables
Create a .env file with:
env# OpenAI (for advanced AI features)
OPENAI_API_KEY=sk-...

# eBay API (for market data)
EBAY_APP_ID=your_app_id
EBAY_CERT_ID=your_cert_id
EBAY_DEV_ID=your_dev_id
EBAY_TOKEN=your_token

# Database
DATABASE_URL=sqlite:///./data/sports_cards.db

# Logging
LOG_LEVEL=INFO
Supported Sports

🏀 NBA (Basketball)
🏒 NHL (Hockey)
⚾ MLB (Baseball)

📈 Example Usage
Python API
pythonfrom src.agents.supervisor_agent import SupervisorAgent
import asyncio

async def analyze_card():
    supervisor = SupervisorAgent()
    
    result = await supervisor.analyze_investment_opportunity(
        player_name="Connor McDavid",
        year=2015,
        manufacturer="Upper Deck",
        sport="NHL",
        budget=2000.0
    )
    
    print(f"Signal: {result['recommendation']['signal']}")
    print(f"Confidence: {result['recommendation']['confidence']}")
    print(f"Reasoning: {result['reasoning']}")

asyncio.run(analyze_card())
Claude Desktop
Analyze a Connor McDavid 2015 Upper Deck rookie card as an investment
🔮 Future Enhancements

 SQLite database for historical tracking
 Real-time player statistics APIs
 Advanced charting and analytics
 Email/SMS alert system
 Portfolio management features
 Machine learning price predictions
 Additional marketplace integrations
 Mobile app
 Docker deployment
 Cloud hosting

🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the repository
Create your feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
🙏 Acknowledgments

LangChain - AI framework
LangGraph - Multi-agent orchestration
Anthropic MCP - Model Context Protocol
Streamlit - Web interface
UV - Package management
eBay Developer Program - Market data

📧 Contact
Your Name - @yourtwitter
Project Link: https://github.com/yourusername/sports-card-ai-agent

Built with ❤️ using AI and modern Python tools