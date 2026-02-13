# AGENTS.md

This file contains guidelines and commands for agentic coding agents working on the Sports Card AI Agent repository.

## Build/Lint/Test Commands

### Development Setup
```bash
# Install dependencies with UV
uv sync

# Install development dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install
```

### Running Tests
```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run with coverage
python -m pytest tests/unit/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/unit/agents/test_trading_strategy_agent.py -v

# Run tests matching pattern
python -m pytest -k "test_generate_strategy" -v

# Run async tests
python -m pytest tests/unit/ -v --asyncio-mode=auto
```

### Linting and Formatting
```bash
# Run ruff linting (with auto-fix)
ruff check src/ tests/ --fix

# Run ruff formatting
ruff format src/ tests/

# Run mypy type checking
mypy src/ --strict --warn-return-any

# Run all linting tools
ruff check src/ tests/ --fix && ruff format src/ tests/ && mypy src/ --strict
```

### Running the Application
```bash
# Web interface
streamlit run app.py

# MCP server
python src/mcp/server.py
```

## Code Style Guidelines

### Import Organization
- Use absolute imports: `from src.agents.market_research_agent import MarketResearchAgent`
- Group imports: standard library, third-party, local
- Use `ruff` for import sorting (I prefix)

### Type Hints
- All functions must have type hints
- Use `dict[str, Any]` for generic dictionaries
- Use `Optional[T]` for nullable types
- Use `|` union syntax (Python 3.13+)
- Pydantic models for data validation

### Naming Conventions
- Classes: `PascalCase` (e.g., `TradingStrategyAgent`)
- Functions/variables: `snake_case` (e.g., `analyze_investment_opportunity`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_RETRY_COUNT`)
- Private methods: prefix with `_` (e.g., `_validate_input`)
- File names: `snake_case.py` (e.g., `market_research_agent.py`)

### Code Structure
- Follow the existing project structure under `src/`
- Agents in `src/agents/`, Tools in `src/tools/`, Models in `src/models/`, Utils in `src/utils/`
- Each module should have a clear purpose and single responsibility
- Use async/await for I/O operations and API calls

### Error Handling
- Use custom exceptions from `src.utils.exceptions`
- Always include context in error messages
- Use structured logging with `src.utils.logging_config`
- Implement circuit breakers for external API calls

### Testing
- All new code must have unit tests
- Use pytest fixtures for common test data
- Mock external API calls
- Test both success and failure scenarios
- Use descriptive test names with `test_` prefix
- Place tests in `tests/unit/` matching the source structure

### Documentation
- Use docstrings for all public classes and methods
- Follow the existing docstring style (Google-style or similar)
- Include type hints in docstring examples
- Use Spanish for user-facing messages, English for code comments

### Configuration
- Use `src.utils.config` for configuration management
- Environment variables in `.env` file
- Use Pydantic for configuration validation
- Default values should be sensible and documented

### Logging
- Use structured JSON logging via `src.utils.logging_config`
- Include context_id for tracking requests
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Never log sensitive information (API keys, personal data)

### Database and Data
- Use SQLAlchemy models in `src.models.db_models`
- Repository pattern for data access (`src.utils.repository`)
- Use transactions for multi-table operations
- Validate data before database operations

### Security
- Never commit API keys or secrets
- Use environment variables for sensitive configuration
- Validate all external inputs
- Use HTTPS for all external API calls
- Implement rate limiting for external APIs

## Project-Specific Patterns

### Agent Pattern
- All agents inherit from a common base or follow similar structure
- Use async methods for long-running operations
- Return structured dictionaries with results
- Handle errors gracefully and return error status

### Tool Pattern
- Tools in `src/tools/` follow a common interface
- Each tool handles a specific external API or data source
- Use caching for expensive operations
- Implement proper error handling and retries

### MCP Integration
- MCP tools defined in `src/mcp/tools.py`
- Server implementation in `src/mcp/server.py`
- Follow MCP protocol specifications
- Expose agents and tools via MCP interface

## Pre-commit Hooks

The project uses pre-commit hooks for code quality:
- Ruff linting and formatting
- Black formatting (fallback)
- MyPy type checking
- Basic file checks (trailing whitespace, large files)

Always run `pre-commit run --all-files` before committing to ensure code quality.