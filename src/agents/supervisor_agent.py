import asyncio
from datetime import datetime
from typing import Any

from src.agents.market_research_agent import MarketResearchAgent
from src.agents.player_analysis_agent import PlayerAnalysisAgent
from src.agents.trading_strategy_agent import TradingStrategyAgent
from src.utils.db_helper import save_analysis_to_db
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class SupervisorAgent:
    """Supervisor que coordina múltiples agentes"""

    def __init__(self):
        self.name = "Supervisor Agent"
        self.market_agent = MarketResearchAgent()
        self.player_agent = PlayerAnalysisAgent()
        self.strategy_agent = TradingStrategyAgent()

    async def analyze_investment_opportunity(
        self,
        player_name: str,
        year: int,
        manufacturer: str = "Topps",
        sport: str = "NBA",
        budget: float = 1000.0,
    ) -> dict[str, Any]:
        """Ejecuta análisis multi-agente completo"""

        logger.info(f"Starting multi-agent analysis for {player_name} {year} ({sport})")

        # Ejecutar análisis en paralelo
        market_task = self.market_agent.research_card_market(
            player_name=player_name, year=year, manufacturer=manufacturer
        )

        player_task = self.player_agent.analyze_player(player_name=player_name, sport=sport)

        try:
            # Esperar a que ambos terminen
            market_analysis, player_analysis = await asyncio.gather(market_task, player_task)
            logger.info("Market and player analysis tasks completed")
        except Exception as e:
            logger.error(f"Error during parallel analysis tasks: {e}", exc_info=True)
            # Return a basic error result
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

        card_info = {
            "player": player_name,
            "year": year,
            "manufacturer": manufacturer,
            "sport": sport,
        }

        try:
            trading_strategy = await self.strategy_agent.generate_trading_strategy(
                market_analysis=market_analysis,
                player_analysis=player_analysis,
                card_info=card_info,
            )
            logger.info("Trading strategy generated")
        except Exception as e:
            logger.error(f"Error generating trading strategy: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Strategy generation failed: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

        # Handle case where strategy generation returned an error
        if trading_strategy.get("strategy") is None:
            return {
                "success": False,
                "error": trading_strategy.get("error", "Strategy generation failed"),
                "timestamp": datetime.now().isoformat(),
            }

        strategy = trading_strategy["strategy"]

        result = {
            "supervisor": self.name,
            "timestamp": datetime.now().isoformat(),
            "card": card_info,
            "recommendation": {
                "signal": strategy["signal"],
                "confidence": strategy["confidence"],
                "price_targets": strategy["price_targets"],
                "risk_reward": strategy["risk_reward"],
            },
            "detailed_analysis": {
                "market": market_analysis,
                "player": player_analysis,
                "strategy": trading_strategy,
            },
            "reasoning": strategy["reasoning"],
            "action_items": strategy["action_items"],
        }

        # Guardar en base de datos - Fixed signature mismatch
        save_analysis_to_db(
            player_name=player_name,
            sport=sport,
            card_info=card_info,
            market=market_analysis,
            performance=player_analysis,
            strategy=trading_strategy,
        )

        return result
