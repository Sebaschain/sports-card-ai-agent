"""Tests for Market Research Agent."""

from unittest.mock import AsyncMock

import pytest

from src.agents.market_research_agent import MarketResearchAgent
from src.tools.ebay_tool import EBayListing, EBaySearchParams


class TestMarketResearchAgent:
    """Test cases for MarketResearchAgent."""

    @pytest.fixture
    def market_agent(self) -> MarketResearchAgent:
        """Create a MarketResearchAgent instance for testing."""
        return MarketResearchAgent()

    @pytest.fixture
    def sample_ebay_listings(self) -> list[EBayListing]:
        """Create sample eBay listing objects."""
        return [
            EBayListing(
                item_id="12345",
                title="LeBron James 2003 Topps Chrome",
                price=599.99,
                currency="USD",
                condition="Used",
                listing_url="https://ebay.com/itm/12345",
                seller_username="seller1",
                location="US",
                sold=True,
            ),
            EBayListing(
                item_id="67890",
                title="LeBron James 2003 Topps Chrome",
                price=649.99,
                currency="USD",
                condition="Used",
                listing_url="https://ebay.com/itm/67890",
                seller_username="seller2",
                location="US",
                sold=True,
            ),
            EBayListing(
                item_id="11111",
                title="LeBron James 2003 Topps Chrome",
                price=499.99,
                currency="USD",
                condition="Used",
                listing_url="https://ebay.com/itm/11111",
                seller_username="seller3",
                location="US",
                sold=True,
            ),
        ]

    def test_agent_initialization(self, market_agent: MarketResearchAgent) -> None:
        """Test that market agent initializes correctly."""
        assert market_agent.name == "Market Research Agent"
        assert market_agent.ebay_tool is not None

    @pytest.mark.asyncio
    async def test_research_card_market_success(
        self,
        market_agent: MarketResearchAgent,
        sample_ebay_listings: list[EBayListing],
    ) -> None:
        """Test successful market research."""
        # Mock eBay tool to return sample listings
        market_agent.ebay_tool.search_cards = AsyncMock(return_value=sample_ebay_listings)

        # Execute research
        result = await market_agent.research_card_market(
            player_name="LeBron James",
            year=2003,
            manufacturer="Topps",
        )

        # Verify results
        assert result["agent"] == "Market Research Agent"
        assert "LeBron James" in result["card"]
        assert result["market_analysis"]["sold_items"]["count"] == 3

        # Verify price calculations
        expected_avg = (599.99 + 649.99 + 499.99) / 3
        actual_avg = result["market_analysis"]["sold_items"]["average_price"]
        assert actual_avg == round(expected_avg, 2)
        assert result["market_analysis"]["sold_items"]["min_price"] == 499.99
        assert result["market_analysis"]["sold_items"]["max_price"] == 649.99

    @pytest.mark.asyncio
    async def test_research_card_market_no_listings(
        self,
        market_agent: MarketResearchAgent,
    ) -> None:
        """Test market research with no sold listings."""
        # Mock eBay tool to return empty list
        market_agent.ebay_tool.search_cards = AsyncMock(return_value=[])

        # Execute research
        result = await market_agent.research_card_market(
            player_name="Unknown Player",
            year=2024,
            manufacturer="Topps",
        )

        # Verify results with no data
        assert result["market_analysis"]["sold_items"]["count"] == 0
        assert result["market_analysis"]["sold_items"]["average_price"] == 0.0
        assert result["market_analysis"]["sold_items"]["min_price"] == 0
        assert result["market_analysis"]["sold_items"]["max_price"] == 0

    @pytest.mark.asyncio
    async def test_search_query_formatting(
        self,
        market_agent: MarketResearchAgent,
        sample_ebay_listings: list[EBayListing],
    ) -> None:
        """Test that search query is formatted correctly."""
        captured_params = None

        async def capture_params(params: EBaySearchParams) -> list[EBayListing]:
            nonlocal captured_params
            captured_params = params
            return sample_ebay_listings

        market_agent.ebay_tool.search_cards = capture_params

        await market_agent.research_card_market(
            player_name="LeBron James",
            year=2003,
            manufacturer="Topps Chrome",
        )

        # Verify query format
        assert "LeBron James" in captured_params.keywords
        assert "2003" in captured_params.keywords
        assert "Topps Chrome" in captured_params.keywords
        assert captured_params.sold_items_only is True
        assert captured_params.max_results == 20

    @pytest.mark.asyncio
    async def test_ebay_api_error_handling(
        self,
        market_agent: MarketResearchAgent,
    ) -> None:
        """Test handling of eBay API errors."""
        # Mock eBay tool to raise an exception
        market_agent.ebay_tool.search_cards = AsyncMock(
            side_effect=Exception("API rate limit exceeded")
        )

        # Execute research and verify error handling
        result = await market_agent.research_card_market(
            player_name="LeBron James",
            year=2003,
            manufacturer="Topps",
        )

        # Should return error info
        assert result["agent"] == "Market Research Agent"


class TestEBaySearchParams:
    """Test cases for EBaySearchParams validation."""

    def test_default_values(self) -> None:
        """Test default parameter values."""
        params = EBaySearchParams(keywords="test")
        assert params.max_results == 10
        assert params.sort_order == "BestMatch"
        assert params.sold_items_only is False

    def test_custom_values(self) -> None:
        """Test custom parameter values."""
        params = EBaySearchParams(
            keywords="LeBron James 2003",
            max_results=50,
            sold_items_only=True,
            min_price=100.0,
            max_price=1000.0,
        )
        assert params.max_results == 50
        assert params.sold_items_only is True
        assert params.min_price == 100.0
        assert params.max_price == 1000.0

    def test_max_results_validation(self) -> None:
        """Test max_results validation."""
        with pytest.raises(ValueError):
            EBaySearchParams(keywords="test", max_results=150)  # > 100

        with pytest.raises(ValueError):
            EBaySearchParams(keywords="test", max_results=0)  # < 1
