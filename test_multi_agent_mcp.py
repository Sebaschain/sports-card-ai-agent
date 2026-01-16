"""Test del sistema multi-agente vía MCP"""
import asyncio
from src.mcp.tools import multi_agent_analysis


async def test():
    print("\n" + "="*70)
    print("🧪 PROBANDO SISTEMA MULTI-AGENTE VÍA MCP")
    print("="*70)
    
    print("\n🎯 Caso: Connor McDavid 2015 Upper Deck")
    print("-"*70)
    
    result = await multi_agent_analysis(
        player_name="Connor McDavid",
        year=2015,
        manufacturer="Upper Deck",
        sport="NHL"
    )
    
    if result["success"]:
        print("\n✅ ANÁLISIS COMPLETADO")
        print(f"\n🤖 Agentes involucrados:")
        for agent in result["agents_involved"]:
            print(f"   • {agent}")
        
        print(f"\n📊 RECOMENDACIÓN:")
        print(f"   🎯 Señal: {result['recommendation']['signal']}")
        print(f"   📈 Confianza: {result['recommendation']['confidence']}")
        print(f"   💰 Precio entrada: ${result['recommendation']['current_price']}")
        print(f"   🎯 Objetivo venta: ${result['recommendation']['target_sell']}")
        
        print(f"\n📈 ANÁLISIS DE MERCADO:")
        print(f"   Items vendidos: {result['market_analysis']['sold_items_count']}")
        print(f"   Precio promedio: ${result['market_analysis']['average_price']}")
        print(f"   Liquidez: {result['market_analysis']['liquidity']}")
        
        print(f"\n🏒 ANÁLISIS DEL JUGADOR:")
        print(f"   Score: {result['player_analysis']['performance_score']}/100")
        print(f"   Rating: {result['player_analysis']['rating']}")
        print(f"   Tendencia: {result['player_analysis']['trend']}")
        print(f"   Outlook: {result['player_analysis']['outlook']}")
        
        print(f"\n💡 RAZONAMIENTO:")
        print(f"   {result['reasoning']}")
        
        print(f"\n✅ ACCIONES RECOMENDADAS:")
        for action in result['action_items']:
            print(f"   • {action}")
    else:
        print(f"\n❌ ERROR: {result.get('error')}")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETADO")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test())