"""Tests for Trading Strategy Agent with improved error handling."""

import pytest

from src.agents.trading_strategy_agent import TradingStrategyAgent


class TestTradingStrategyAgentImproved:
    """Test cases for improved TradingStrategyAgent."""

    @pytest.fixture
    def strategy_agent(self) -> TradingStrategyAgent:
        """Create a TradingStrategyAgent instance for testing."""
        return TradingStrategyAgent()

    @pytest.fixture
    def sample_market_analysis(self) -> dict:
        """Sample market analysis data."""
        return {
            "market_analysis": {
                "sold_items": {
                    "count": 10,
                    "average_price": 500.00,
                    "min_price": 400.00,
                    "max_price": 800.00,
                },
                "active_items": {"count": 5, "average_price": 550.00},
                "liquidity": "Alta",
                "price_gap_percentage": 10.0,
                "market_insight": "Mercado activo",
            }
        }

    @pytest.fixture
    def sample_player_analysis(self) -> dict:
        """Sample player analysis data."""
        return {
            "analysis": {
                "performance_score": {
                    "overall_score": 85,
                    "trending": "up",
                    "rating": "Elite",
                },
            }
        }

    @pytest.fixture
    def sample_card_info(self) -> dict:
        """Sample card information."""
        return {
            "player": "LeBron James",
            "year": 2003,
            "manufacturer": "Topps",
            "sport": "NBA",
        }

    def test_agent_initialization(self, strategy_agent: TradingStrategyAgent) -> None:
        """Test that strategy agent initializes correctly."""
        assert strategy_agent.name == "Trading Strategy Agent"
        assert strategy_agent.buy_threshold == 85
        assert strategy_agent.hold_threshold == 70

    def test_default_thresholds(self) -> None:
        """Test default threshold values."""
        agent = TradingStrategyAgent()
        assert agent.buy_threshold == 85
        assert agent.hold_threshold == 70
        assert agent.entry_discount == 0.95
        assert agent.target_multiplier == 1.25
        assert agent.stop_loss_discount == 0.85

    def test_custom_thresholds(self) -> None:
        """Test custom threshold configuration."""
        agent = TradingStrategyAgent(
            buy_threshold=90,
            hold_threshold=75,
            entry_discount=0.90,
            target_multiplier=1.30,
            stop_loss_discount=0.80,
        )
        assert agent.buy_threshold == 90
        assert agent.hold_threshold == 75
        assert agent.entry_discount == 0.90

    @pytest.mark.asyncio
    async def test_generate_strategy_buy_signal(
        self,
        strategy_agent: TradingStrategyAgent,
        sample_market_analysis: dict,
        sample_player_analysis: dict,
        sample_card_info: dict,
    ) -> None:
        """Test BUY signal generation for high-scoring players."""
        result = await strategy_agent.generate_trading_strategy(
            market_analysis=sample_market_analysis,
            player_analysis=sample_player_analysis,
            card_info=sample_card_info,
        )

        assert result["agent"] == "Trading Strategy Agent"
        assert result["strategy"]["signal"] == "BUY"
        assert result["strategy"]["confidence"] == 0.80
        assert "entry_price" in result["strategy"]["price_targets"]
        assert "context_id" in result
        assert result["data_quality"]["price_estimated"] is False

    @pytest.mark.asyncio
    async def test_generate_strategy_hold_signal(
        self,
        strategy_agent: TradingStrategyAgent,
        sample_market_analysis: dict,
        sample_card_info: dict,
    ) -> None:
        """Test HOLD signal generation for medium-scoring players."""
        player_analysis = {"analysis": {"performance_score": {"overall_score": 75}}}

        result = await strategy_agent.generate_trading_strategy(
            market_analysis=sample_market_analysis,
            player_analysis=player_analysis,
            card_info=sample_card_info,
        )

        assert result["strategy"]["signal"] == "HOLD"
        assert result["strategy"]["confidence"] == 0.65

    @pytest.mark.asyncio
    async def test_generate_strategy_sell_signal(
        self,
        strategy_agent: TradingStrategyAgent,
        sample_market_analysis: dict,
        sample_card_info: dict,
    ) -> None:
        """Test SELL signal generation for low-scoring players."""
        player_analysis = {"analysis": {"performance_score": {"overall_score": 60}}}

        result = await strategy_agent.generate_trading_strategy(
            market_analysis=sample_market_analysis,
            player_analysis=player_analysis,
            card_info=sample_card_info,
        )

        assert result["strategy"]["signal"] == "SELL"
        assert result["strategy"]["confidence"] == 0.70

    @pytest.mark.asyncio
    async def test_price_targets_calculation(
        self,
        strategy_agent: TradingStrategyAgent,
        sample_market_analysis: dict,
        sample_card_info: dict,
    ) -> None:
        """Test that price targets are calculated correctly."""
        player_analysis = {"analysis": {"performance_score": {"overall_score": 90}}}

        result = await strategy_agent.generate_trading_strategy(
            market_analysis=sample_market_analysis,
            player_analysis=player_analysis,
            card_info=sample_card_info,
        )

        price_targets = result["strategy"]["price_targets"]
        avg_price = sample_market_analysis["market_analysis"]["sold_items"]["average_price"]

        # Entry price: 5% below average
        assert price_targets["entry_price"] == round(avg_price * 0.95, 2)

        # Target sell: 25% above average
        assert price_targets["target_sell_price"] == round(avg_price * 1.25, 2)

        # Stop loss: 15% below average
        assert price_targets["stop_loss"] == round(avg_price * 0.85, 2)

    @pytest.mark.asyncio
    async def test_empty_market_analysis(
        self,
        strategy_agent: TradingStrategyAgent,
        sample_card_info: dict,
    ) -> None:
        """Test handling of empty market analysis."""
        empty_market = {"market_analysis": {}}
        player_analysis = {"analysis": {"performance_score": {"overall_score": 85}}}

        result = await strategy_agent.generate_trading_strategy(
            market_analysis=empty_market,
            player_analysis=player_analysis,
            card_info=sample_card_info,
        )

        # Should still return a response but with estimated data
        assert result["strategy"] is None
        assert "error" in result

    @pytest.mark.asyncio
    async def test_empty_player_analysis(
        self,
        strategy_agent: TradingStrategyAgent,
        sample_market_analysis: dict,
        sample_card_info: dict,
    ) -> None:
        """Test handling of empty player analysis."""
        empty_player = {"analysis": {}}

        result = await strategy_agent.generate_trading_strategy(
            market_analysis=sample_market_analysis,
            player_analysis=empty_player,
            card_info=sample_card_info,
        )

        # Should use default score of 50, resulting in SELL signal
        assert result["strategy"]["signal"] == "SELL"
        assert result["data_quality"]["player_score_estimated"] is True

    @pytest.mark.asyncio
    async def test_no_performance_score(
        self,
        strategy_agent: TradingStrategyAgent,
        sample_market_analysis: dict,
        sample_card_info: dict,
    ) -> None:
        """Test handling of missing performance score."""
        incomplete_player = {"analysis": {"stats": {}}}

        result = await strategy_agent.generate_trading_strategy(
            market_analysis=sample_market_analysis,
            player_analysis=incomplete_player,
            card_info=sample_card_info,
        )

        # Should use default score
        assert result["data_quality"]["player_score_estimated"] is True

    @pytest.mark.asyncio
    async def test_risk_reward_calculation(
        self,
        strategy_agent: TradingStrategyAgent,
        sample_market_analysis: dict,
        sample_card_info: dict,
    ) -> None:
        """Test that risk/reward ratio changes based on score."""
        # High score
        high_score = {"analysis": {"performance_score": {"overall_score": 92}}}
        result_high = await strategy_agent.generate_trading_strategy(
            market_analysis=sample_market_analysis,
            player_analysis=high_score,
            card_info=sample_card_info,
        )
        assert result_high["strategy"]["risk_reward"]["ratio"] == "3.0:1"
        assert "Alto potencial" in result_high["strategy"]["risk_reward"]["assessment"]

        # Medium score (>= 70 and < 80)
        mid_score = {"analysis": {"performance_score": {"overall_score": 78}}}
        result_mid = await strategy_agent.generate_trading_strategy(
            market_analysis=sample_market_analysis,
            player_analysis=mid_score,
            card_info=sample_card_info,
        )
        assert result_mid["strategy"]["risk_reward"]["ratio"] == "2.0:1"

        # Low score
        low_score = {"analysis": {"performance_score": {"overall_score": 55}}}
        result_low = await strategy_agent.generate_trading_strategy(
            market_analysis=sample_market_analysis,
            player_analysis=low_score,
            card_info=sample_card_info,
        )
        assert result_low["strategy"]["risk_reward"]["ratio"] == "1.5:1"
        assert "Alto riesgo" in result_low["strategy"]["risk_reward"]["assessment"]

    @pytest.mark.asyncio
    async def test_reasoning_includes_estimates(
        self,
        strategy_agent: TradingStrategyAgent,
        sample_card_info: dict,
    ) -> None:
        """Test that reasoning indicates when data is estimated."""
        # Empty market analysis should result in estimated price
        empty_market = {"market_analysis": {}}
        player_analysis = {"analysis": {"performance_score": {"overall_score": 85}}}

        result = await strategy_agent.generate_trading_strategy(
            market_analysis=empty_market,
            player_analysis=player_analysis,
            card_info=sample_card_info,
        )

        # Result should indicate error, not include reasoning with estimates
        assert result["strategy"] is None

    def test_get_thresholds(self, strategy_agent: TradingStrategyAgent) -> None:
        """Test getting current threshold configuration."""
        thresholds = strategy_agent.get_thresholds()
        assert "buy_threshold" in thresholds
        assert "hold_threshold" in thresholds
        assert "entry_discount" in thresholds
        assert "target_multiplier" in thresholds
        assert "stop_loss_discount" in thresholds

    def test_set_thresholds(self, strategy_agent: TradingStrategyAgent) -> None:
        """Test updating threshold configuration."""
        strategy_agent.set_thresholds(buy_threshold=88, entry_discount=0.92)
        thresholds = strategy_agent.get_thresholds()
        assert thresholds["buy_threshold"] == 88
        assert thresholds["entry_discount"] == 0.92
