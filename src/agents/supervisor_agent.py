import asyncio
from typing import Dict, Any
from datetime import datetime

from src.agents.market_research_agent import MarketResearchAgent
from src.agents.player_analysis_agent import PlayerAnalysisAgent
from src.agents.trading_strategy_agent import TradingStrategyAgent
from src.utils.db_helper import save_analysis_to_db


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
    ) -> Dict[str, Any]:
        """Ejecuta análisis multi-agente completo"""

        print("\n" + "=" * 70)
        print("🤖 SUPERVISOR - Iniciando análisis multi-agente")
        print(f"📋 Tarjeta: {player_name} {year} {manufacturer} ({sport})")
        print("=" * 70)

        print(
            "\n🔍 Iniciando investigación de mercado y análisis de jugador en paralelo..."
        )

        # Ejecutar análisis en paralelo
        market_task = self.market_agent.research_card_market(
            player_name=player_name, year=year, manufacturer=manufacturer
        )

        player_task = self.player_agent.analyze_player(
            player_name=player_name, sport=sport
        )

        # Esperar a que ambos terminen
        market_analysis, player_analysis = await asyncio.gather(
            market_task, player_task
        )

        print("   ✅ Análisis de mercado y de jugador completados")

        print(f"\n📈 {self.strategy_agent.name} - Generando estrategia...")
        card_info = {
            "player": player_name,
            "year": year,
            "manufacturer": manufacturer,
            "sport": sport,
        }

        trading_strategy = self.strategy_agent.generate_trading_strategy(
            market_analysis=market_analysis,
            player_analysis=player_analysis,
            card_info=card_info,
        )
        print("   ✅ Estrategia de trading generada")

        print("\n" + "=" * 70)
        print("✅ ANÁLISIS COMPLETO")
        print("=" * 70)

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

        # Guardar en base de datos
        save_analysis_to_db(
            player_name=player_name,
            year=year,
            manufacturer=manufacturer,
            sport=sport,
            analysis_result=result,
            analysis_type="multi_agent",
        )

        return result
