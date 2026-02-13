"""Tests for Supervisor Agent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.supervisor_agent import SupervisorAgent


class TestSupervisorAgent:
    """Test cases for SupervisorAgent."""

    @pytest.fixture
    def supervisor_agent(self) -> SupervisorAgent:
        """Create a SupervisorAgent instance for testing."""
        return SupervisorAgent()

    @pytest.mark.asyncio
    async def test_supervisor_agent_initialization(self, supervisor_agent: SupervisorAgent) -> None:
        """Test that supervisor agent initializes correctly."""
        assert supervisor_agent.name == "Supervisor Agent"
        assert supervisor_agent.market_agent is not None
        assert supervisor_agent.player_agent is not None
        assert supervisor_agent.strategy_agent is not None

    @pytest.mark.asyncio
    async def test_analyze_investment_opportunity_success(
        self,
        supervisor_agent: SupervisorAgent,
        mock_market_analysis: dict,
        mock_player_analysis: dict,
        mock_card_info: dict,
    ) -> None:
        """Test successful investment opportunity analysis."""
        # Mock the agents' methods
        supervisor_agent.market_agent.research_card_market = AsyncMock(
            return_value=mock_market_analysis
        )
        supervisor_agent.player_agent.analyze_player = AsyncMock(return_value=mock_player_analysis)
        supervisor_agent.strategy_agent.generate_trading_strategy = AsyncMock(
            return_value={
                "agent": "Trading Strategy Agent",
                "timestamp": "2025-02-09T19:00:00Z",
                "card": {"player": "LeBron James"},
                "strategy": {
                    "signal": "BUY",
                    "confidence": 0.85,
                    "price_targets": {
                        "entry_price": 475.0,
                        "target_sell_price": 625.0,
                        "stop_loss": 425.0,
                    },
                    "risk_reward": {"ratio": "2.5:1", "assessment": "Favorable"},
                    "reasoning": "Test reasoning",
                    "action_items": ["Test action 1", "Test action 2"],
                },
            }
        )

        # Mock database save function
        with patch("src.agents.supervisor_agent.save_analysis_to_db") as mock_save:
            # Execute the analysis
            result = await supervisor_agent.analyze_investment_opportunity(
                player_name="LeBron James",
                year=2003,
                manufacturer="Topps",
                sport="NBA",
                budget=1000.0,
            )

        # Verify the result structure
        assert result["supervisor"] == "Supervisor Agent"
        assert result["recommendation"]["signal"] == "BUY"
        assert result["recommendation"]["confidence"] == 0.85
        assert result["card"]["player"] == "LeBron James"

    @pytest.mark.asyncio
    async def test_analyze_investment_opportunity_market_error(
        self,
        supervisor_agent: SupervisorAgent,
        mock_player_analysis: dict,
    ) -> None:
        """Test handling of market agent error."""
        # Mock the market agent to raise an error
        supervisor_agent.market_agent.research_card_market = AsyncMock(
            side_effect=Exception("API timeout")
        )
        supervisor_agent.player_agent.analyze_player = AsyncMock(return_value=mock_player_analysis)

        # Execute the analysis
        result = await supervisor_agent.analyze_investment_opportunity(
            player_name="LeBron James",
            year=2003,
            manufacturer="Topps",
            sport="NBA",
            budget=1000.0,
        )

        # Verify error handling
        assert result["success"] is False
        assert "error" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_analyze_investment_opportunity_player_error(
        self,
        supervisor_agent: SupervisorAgent,
        mock_market_analysis: dict,
    ) -> None:
        """Test handling of player agent error."""
        # Mock the player agent to raise an error
        supervisor_agent.market_agent.research_card_market = AsyncMock(
            return_value=mock_market_analysis
        )
        supervisor_agent.player_agent.analyze_player = AsyncMock(
            side_effect=Exception("Player not found")
        )

        # Execute the analysis
        result = await supervisor_agent.analyze_investment_opportunity(
            player_name="Unknown Player",
            year=2024,
            manufacturer="Topps",
            sport="NBA",
            budget=1000.0,
        )

        # Verify error handling
        assert result["success"] is False
        assert "error" in result


class TestSupervisorAgentIntegration:
    """Integration tests for SupervisorAgent with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_parallel_execution_of_agents(
        self,
        mock_market_analysis: dict,
        mock_player_analysis: dict,
    ) -> None:
        """Test that supervisor coordinates agents correctly."""

        async def mock_market_research(*args, **kwargs):
            return mock_market_analysis

        async def mock_player_analysis(*args, **kwargs):
            return mock_player_analysis

        async def mock_strategy(*args, **kwargs):
            return {
                "agent": "Trading Strategy Agent",
                "strategy": {
                    "signal": "HOLD",
                    "confidence": 0.65,
                    "price_targets": {
                        "entry_price": 475.0,
                        "target_sell_price": 625.0,
                        "stop_loss": 425.0,
                    },
                    "risk_reward": {"ratio": "2.5:1", "assessment": "Favorable"},
                    "reasoning": "Test reasoning",
                    "action_items": ["Test action 1"],
                },
            }

        with patch.object(
            SupervisorAgent,
            "__init__",
            lambda x: None,
        ):
            agent = SupervisorAgent()
            agent.name = "Supervisor Agent"
            agent.market_agent = MagicMock()
            agent.market_agent.research_card_market = mock_market_research
            agent.player_agent = MagicMock()
            agent.player_agent.analyze_player = mock_player_analysis
            agent.strategy_agent = MagicMock()
            agent.strategy_agent.generate_trading_strategy = mock_strategy

            with patch("src.agents.supervisor_agent.save_analysis_to_db"):
                result = await agent.analyze_investment_opportunity(
                    player_name="Test Player",
                    year=2024,
                )

            # Verify supervisor coordinated correctly
            assert result["supervisor"] == "Supervisor Agent"
            assert result["recommendation"]["signal"] == "HOLD"
            assert result["recommendation"]["confidence"] == 0.65
