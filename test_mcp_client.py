"""
Cliente de prueba para el servidor MCP
"""
import asyncio
from src.mcp.tools import (
    search_sports_cards,
    analyze_card_investment,
    get_player_card_recommendations,
    compare_card_prices
)


async def test_all_tools():
    """Prueba todas las herramientas MCP"""
    print("\n" + "="*70)
    print("🧪 PROBANDO HERRAMIENTAS MCP")
    print("="*70 + "\n")
    
    # Test 1: Buscar tarjetas
    print("1️⃣ Test: search_sports_cards")
    print("-" * 70)
    result1 = await search_sports_cards(
        keywords="LeBron James 2003 rookie",
        max_results=3
    )
    print(f"✅ Éxito: {result1['success']}")
    print(f"📊 Resultados: {result1['results_count']}")
    if result1['success'] and result1['listings']:
        print(f"💰 Primer resultado: {result1['listings'][0]['title'][:60]}...")
    print()
    
    # Test 2: Analizar inversión
    print("2️⃣ Test: analyze_card_investment")
    print("-" * 70)
    result2 = await analyze_card_investment(
        player_name="Connor McDavid",
        year=2015,
        manufacturer="Upper Deck",
        sport="NHL"
    )
    print(f"✅ Éxito: {result2['success']}")
    if result2['success']:
        analysis = result2['analysis']
        print(f"🎯 Señal: {analysis['signal'].upper()}")
        print(f"📊 Confianza: {analysis['confidence']}%")
        print(f"💡 Razón: {analysis['reasoning'][:80]}...")
    print()
    
    # Test 3: Recomendaciones
    print("3️⃣ Test: get_player_card_recommendations")
    print("-" * 70)
    result3 = await get_player_card_recommendations(
        player_name="Mike Trout",
        sport="MLB",
        budget=800.0
    )
    print(f"✅ Éxito: {result3['success']}")
    if result3['success'] and 'recommendations' in result3:
        print(f"🎁 Recomendaciones: {len(result3['recommendations'])}")
        if result3['recommendations']:
            rec = result3['recommendations'][0]
            print(f"💎 Top recomendación: ${rec['price']:.2f} - {rec['title'][:50]}...")
    print()
    
    # Test 4: Comparar precios
    print("4️⃣ Test: compare_card_prices")
    print("-" * 70)
    result4 = await compare_card_prices(
        player_name="Patrick Mahomes",
        year=2017,
        manufacturer="Panini"
    )
    print(f"✅ Éxito: {result4['success']}")
    if result4['success']:
        print(f"📈 Items vendidos: {result4['sold_items']['count']}")
        print(f"💰 Promedio vendidos: ${result4['sold_items']['average_price']:.2f}")
        print(f"🔵 Items activos: {result4['active_items']['count']}")
        print(f"💵 Promedio activos: ${result4['active_items']['average_price']:.2f}")
        if 'price_difference_pct' in result4:
            print(f"📊 Diferencia: {result4['price_difference_pct']:+.1f}%")
    print()
    
    print("="*70)
    print("✅ TODAS LAS HERRAMIENTAS PROBADAS")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_all_tools())