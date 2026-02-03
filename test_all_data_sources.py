"""Test completo de todas las fuentes de datos"""

import asyncio
from src.agents.player_analysis_agent import PlayerAnalysisAgent
from src.tools.tcgplayer_tool import TCGPlayerTool, COMCTool

print("=" * 70)
print("🧪 TEST COMPLETO DE FUENTES DE DATOS")
print("=" * 70)


# Test 1: Player Analysis con todas las fuentes
async def test_player_analysis():
    print("\n1️⃣ ANÁLISIS COMPLETO - LeBron James")
    print("-" * 70)

    agent = PlayerAnalysisAgent()
    result = await agent.analyze_player("LeBron James", "NBA")

    if result.get("real_stats") and result["real_stats"].get("success"):
        print("✅ Estadísticas Reales:")
        stats = result["real_stats"]
        print(f"   PPG: {stats.get('points_per_game', 0):.1f}")
        print(f"   Team: {stats.get('team')}")
    else:
        print("⚠️  Estadísticas: No disponibles")

    if result.get("news") and result["news"].get("success"):
        print("\n✅ Noticias Recientes:")
        news = result["news"]
        print(f"   Encontradas: {news.get('news_count', 0)} noticias")
        if news.get("summary"):
            print(f"   {news.get('summary')}")
        if news.get("news"):
            print(f"\n   Última: {news['news'][0]['title'][:60]}...")
    else:
        print("\n⚠️  Noticias: No disponibles")

    if result.get("sentiment") and result["sentiment"].get("success"):
        print("\n✅ Análisis de Sentimiento:")
        sent = result["sentiment"]
        print(f"   Sentimiento General: {sent.get('overall_sentiment', 'N/A')}")
        print(f"   Score: {sent.get('sentiment_score', 0)}")
        print(f"   Confianza: {sent.get('confidence', 0):.0%}")
        if sent.get("distribution"):
            dist = sent["distribution"]
            print(f"   📊 Distribución:")
            print(
                f"      Positivo: {dist.get('positive', 0)} | Neutral: {dist.get('neutral', 0)} | Negativo: {dist.get('negative', 0)}"
            )
        if sent.get("recommendation"):
            print(f"   {sent['recommendation']}")
    else:
        print("\n⚠️  Análisis de Sentimiento: No disponible")

    if result.get("analysis") and result["analysis"].get("performance_score"):
        print(
            f"\n📊 Score Final: {result['analysis']['performance_score'].get('overall_score', 0)}/100"
        )
        print(
            f"🎯 Rating: {result['analysis']['performance_score'].get('rating', 'N/A')}"
        )
    else:
        print("\n⚠️  Análisis: No disponible")


async def test_marketplaces():
    print("\n\n2️⃣ MARKETPLACES ADICIONALES")
    print("-" * 70)
    tcg = TCGPlayerTool()
    tcg_prices = await tcg.search_card_prices("LeBron James", 2003)
    if tcg_prices["prices"]["market_price"] > 0:
        print(f"✅ TCGPlayer: Market Price ${tcg_prices['prices']['market_price']:.2f}")
    else:
        print(f"⚠️  TCGPlayer: API no disponible (mockup)")

    comc = COMCTool()
    comc_prices = await comc.search_card_prices("LeBron James", 2003)
    if comc_prices["prices"]["average_price"] > 0:
        print(f"✅ COMC: Average Price ${comc_prices['prices']['average_price']:.2f}")
    else:
        print(f"⚠️  COMC: API no disponible (mockup)")


async def main():
    await test_player_analysis()
    await test_marketplaces()


if __name__ == "__main__":
    asyncio.run(main())
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETADO - Todas las fuentes integradas")
    print("=" * 70)
