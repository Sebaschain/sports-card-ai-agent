"""Test simple de los agentes"""
import asyncio

print("="*60)
print("🧪 Iniciando test de agentes...")
print("="*60)

async def test():
    print("\n1. Importando Market Agent...")
    from src.agents.market_research_agent import MarketResearchAgent
    market_agent = MarketResearchAgent()
    print(f"   ✅ {market_agent.name}")
    
    print("\n2. Importando Player Agent...")
    from src.agents.player_analysis_agent import PlayerAnalysisAgent
    player_agent = PlayerAnalysisAgent()
    print(f"   ✅ {player_agent.name}")
    
    print("\n3. Importando Trading Agent...")
    from src.agents.trading_strategy_agent import TradingStrategyAgent
    trading_agent = TradingStrategyAgent()
    print(f"   ✅ {trading_agent.name}")
    
    print("\n4. Probando Player Agent...")
    result = player_agent.analyze_player(
        player_name="Connor McDavid",
        sport="NHL",
        current_performance="Excelente temporada, promediando 1.5 puntos por partido"
    )
    print(f"   ✅ Análisis completado")
    print(f"   📊 Score: {result['analysis']['performance_score']['overall_score']}")
    print(f"   🎯 Rating: {result['analysis']['performance_score']['rating']}")
    print(f"   📈 Outlook: {result['analysis']['future_outlook']}")
    
    print("\n5. Importando Supervisor Agent...")
    from src.agents.supervisor_agent import SupervisorAgent
    supervisor = SupervisorAgent()
    print(f"   ✅ {supervisor.name}")
    
    print("\n" + "="*60)
    print("✅ TODOS LOS AGENTES FUNCIONAN")
    print("="*60)
    
    print("\n6. Probando sistema completo...")
    print("-"*60)
    
    result = await supervisor.analyze_investment_opportunity(
        player_name="Connor McDavid",
        year=2015,
        manufacturer="Upper Deck",
        sport="NHL",
        budget=2000.0
    )
    
    print("\n📊 REPORTE FINAL:")
    print(f"🎯 Señal: {result['recommendation']['signal']}")
    print(f"📈 Confianza: {result['recommendation']['confidence']:.0%}")
    print(f"💰 Precio entrada: ${result['recommendation']['price_targets']['entry_price']}")
    print(f"🎯 Precio objetivo: ${result['recommendation']['price_targets']['target_sell_price']}")
    print(f"\n💡 Razonamiento:\n{result['reasoning']}")
    print(f"\n✅ Acciones:")
    for action in result['action_items']:
        print(f"   • {action}")
    
    print("\n" + "="*60)
    print("🎉 SISTEMA MULTI-AGENTE COMPLETO Y FUNCIONAL")
    print("="*60)

asyncio.run(test())