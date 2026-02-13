"""
Utility for real-time synchronization of market prices
"""

import asyncio
from typing import Dict, Any
from datetime import datetime

from src.utils.database import get_db
from src.agents.market_research_agent import MarketResearchAgent
from src.models.db_models import PortfolioItemDB, WatchlistDB, CardDB, PlayerDB
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class RealtimeSync:
    """Handles batch updates of market prices"""

    def __init__(self):
        self.market_agent = MarketResearchAgent()

    async def sync_portfolio(self, user_id: int) -> Dict[str, Any]:
        """Update market values for all active portfolio items for a user"""
        logger.info(f"Starting real-time portfolio sync for user {user_id}")

        with get_db() as db:
            active_items = (
                db.query(PortfolioItemDB, CardDB, PlayerDB)
                .join(CardDB, PortfolioItemDB.card_id == CardDB.id)
                .join(PlayerDB, CardDB.player_id == PlayerDB.id)
                .filter(PortfolioItemDB.user_id == user_id)
                .filter(PortfolioItemDB.is_active)
                .all()
            )

            results = {
                "total": len(active_items),
                "updated": 0,
                "errors": 0,
                "details": [],
            }

            for p_item, card, player in active_items:
                try:
                    # Fetch latest market data
                    analysis = await self.market_agent.research_card_market(
                        player_name=player.name,
                        year=card.year,
                        manufacturer=card.manufacturer,
                    )

                    new_price = analysis["market_analysis"]["sold_items"][
                        "average_price"
                    ]

                    if new_price > 0:
                        p_item.current_value = new_price
                        p_item.last_updated = datetime.now()
                        results["updated"] += 1
                        results["details"].append(
                            f"✅ {player.name} {card.year}: ${new_price:.2f}"
                        )
                    else:
                        results["details"].append(
                            f"ℹ️ {player.name} {card.year}: No price found"
                        )

                except Exception as e:
                    logger.error(f"Error syncing {player.name}: {e}")
                    results["errors"] += 1
                    results["details"].append(f"❌ {player.name}: {str(e)}")

                # Throttling to avoid eBay rate limits
                await asyncio.sleep(1.0)

            db.commit()
            logger.info(
                f"Portfolio sync completed for user {user_id}. Updated {results['updated']} items."
            )
            return results

    async def sync_watchlist(self, user_id: int) -> Dict[str, Any]:
        """Update market values for all watchlist items for a user"""
        logger.info(f"Starting real-time watchlist sync for user {user_id}")

        with get_db() as db:
            items = (
                db.query(WatchlistDB, CardDB, PlayerDB)
                .join(CardDB, WatchlistDB.card_id == CardDB.id)
                .join(PlayerDB, CardDB.player_id == PlayerDB.id)
                .filter(WatchlistDB.user_id == user_id)
                .all()
            )

            results = {"total": len(items), "updated": 0, "errors": 0, "details": []}

            for watch_item, card, player in items:
                try:
                    analysis = await self.market_agent.research_card_market(
                        player_name=player.name,
                        year=card.year,
                        manufacturer=card.manufacturer,
                    )

                    new_price = analysis["market_analysis"]["sold_items"][
                        "average_price"
                    ]

                    if new_price > 0:
                        watch_item.last_price = new_price
                        watch_item.last_updated = datetime.now()
                        results["updated"] += 1
                        results["details"].append(
                            f"✅ {player.name} {card.year}: ${new_price:.2f}"
                        )

                except Exception as e:
                    logger.error(f"Error syncing watchlist item {player.name}: {e}")
                    results["errors"] += 1

                await asyncio.sleep(1.0)

            db.commit()
            return results
