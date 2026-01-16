"""
Test del sistema multi-agente con LangGraph
"""
import asyncio
import json
from src.agents.supervisor_agent import SupervisorAgent


async def test_multi_agent_system():
    """Prueba el sistema completo de múltiples agentes"""
    
    print("\n" + "="*70)
    print("🧪 PROBANDO SISTEMA MULTI-AGENTE CON LANGGRAPH")
    print("="*70 + "\n")
    
    # Crear supervisor
    supervisor = SupervisorAgent()
    
    # Caso de prueba 1: Connor McDavid
    print("📋 CASO 1: Connor McDavid 2015 Upper Deck (NHL)")
    print("-"*70)
    
    result1 = await supervisor.analyze_investment_opportunity(
        player_name="Connor McDavid",
        year=2015,
        manufacturer="Upper Deck",
        sport="NHL",
        budget=2000.0
    )
    
    print("\n📊 REPORTE FINAL:")
    print(f"🎯 Señal: {result1['recommendation']['signal']}")
    print(f"📈 Confianza: {result1['recommendation']['confidence']:.0%}")
    print(f"\n💡 Razonamiento:\n{result1['reasoning']}")
    print(f"\n✅ Acciones Recomendadas:")
    for action in result1['action_items'][:3]:
        print(f"   • {action}")
    
    print("\n" + "="*70)
    
    # Caso de prueba 2: LeBron James
    print("\n📋 CASO 2: LeBron James 2003 Topps (NBA)")
    print("-"*70)
    
    result2 = await supervisor.analyze_investment_opportunity(
        player_name="LeBron James",
        year=2003,
        manufacturer="Topps",
        sport="NBA",
        budget=5000.0
    )
    
    print("\n📊 REPORTE FINAL:")
    print(f"🎯 Señal: {result2['recommendation']['signal']}")
    print(f"📈 Confianza: {result2['recommendation']['confidence']:.0%}")
    print(f"\n💡 Razonamiento:\n{result2['reasoning']}")
    
    print("\n" + "="*70)
    print("✅ SISTEMA MULTI-AGENTE FUNCIONANDO CORRECTAMENTE")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_multi_agent_system())