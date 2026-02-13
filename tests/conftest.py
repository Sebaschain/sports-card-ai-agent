"""
Pytest configuration and fixtures for Sports Card AI Agent tests.
"""

import asyncio
from collections.abc import Generator

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_ebay_response() -> list:
    """Mock eBay search response."""
    return [
        {
            "item_id": "12345",
            "title": "LeBron James 2003 Topps Chrome Rookie Card",
            "price": 599.99,
            "currency": "USD",
            "condition": "Used",
            "listing_url": "https://ebay.com/itm/12345",
            "image_url": None,
            "seller_username": "seller123",
            "location": "US",
            "sold": True,
        },
        {
            "item_id": "67890",
            "title": "LeBron James 2003 Topps Chrome Rookie Card",
            "price": 649.99,
            "currency": "USD",
            "condition": "Used",
            "listing_url": "https://ebay.com/itm/67890",
            "image_url": None,
            "seller_username": "seller456",
            "location": "US",
            "sold": True,
        },
    ]


@pytest.fixture
def mock_nba_player_stats() -> dict:
    """Mock NBA player statistics response."""
    return {
        "success": True,
        "player_id": 2544,
        "player_name": "LeBron James",
        "career_averages": {
            "points": 27.2,
            "rebounds": 7.5,
            "assists": 7.3,
            "games_played": 1421,
        },
        "season_stats": {
            "year": "2024-25",
            "points": 25.4,
            "rebounds": 7.2,
            "assists": 8.1,
            "games_played": 55,
        },
    }


@pytest.fixture
def mock_market_analysis() -> dict:
    """Mock market analysis response."""
    return {
        "agent": "Market Research Agent",
        "card": "LeBron James 2003 Topps",
        "timestamp": "2025-02-09T19:00:00Z",
        "market_analysis": {
            "sold_items": {
                "count": 10,
                "average_price": 549.99,
                "min_price": 399.99,
                "max_price": 899.99,
            },
            "active_items": {"count": 5, "average_price": 625.00},
            "liquidity": "Alta",
            "price_gap_percentage": 12.5,
            "market_insight": "Mercado activo con buena demanda",
        },
    }


@pytest.fixture
def mock_player_analysis() -> dict:
    """Mock player analysis response."""
    return {
        "agent": "Player Analysis Agent",
        "player": "LeBron James",
        "sport": "NBA",
        "timestamp": "2025-02-09T19:00:00Z",
        "analysis": {
            "performance_score": {
                "overall_score": 92,
                "trending": "up",
                "rating": "Elite",
            },
            "career_highlights": [
                "4x NBA Champion",
                "4x NBA MVP",
                "All-Star selections: 20",
            ],
        },
    }


@pytest.fixture
def mock_card_info() -> dict:
    """Mock card information."""
    return {
        "player": "LeBron James",
        "year": 2003,
        "manufacturer": "Topps",
        "sport": "NBA",
    }
