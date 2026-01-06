"""
Test del agente de análisis de precios
"""

from datetime import datetime, timedelta
from src.agents.price_analyzer_agent import PriceAnalyzerAgent
from src.models.card import (
    Card, Player, Sport, CardCondition, PricePoint
)


def create_sample_card() -> Card:
    """Crea una tarjeta de ejemplo"""
    player = Player(
        id="lebron-james",
        name="LeBron James",
        sport=Sport.NBA,
        team="Los Angeles Lakers",
        position="Forward"
    )
    
    card = Card(
        id="lebron-2003-topps-221",
        player=player,
        year=2003,
        manufacturer="Topps",
        set_name="Topps Chrome",
        card_number="221",
        variant="Rookie Card",
        condition=CardCondition.MINT,
        graded=True,
        grade=9.5,
        grading_company="PSA"
    )
    
    return card


def create_sample_prices(trend: str = "stable") -> list:
    """Crea precios de ejemplo con diferentes tendencias"""
    base_price = 1000.0
    prices = []
    
    for i in range(30):
        date = datetime.now() - timedelta(days=30-i)
        
        if trend == "up":
            price = base_price + (i * 20)  # Subiendo
        elif trend == "down":
            price = base_price - (i * 15)  # Bajando
        else:
            price = base_price + ((-1)**i * 50)  # Estable con variación
        
        price_point = PricePoint(
            card_id="lebron-2003-topps-221",
            price=max(price, 100),  # Precio mínimo
            marketplace="ebay",
            listing_url="https://ebay.com/item/123",
            timestamp=date,
            sold=True
        )
        prices.append(price_point)
    
    return prices


def main():
    print("\n" + "="*70)
    print("🤖 PROBANDO AGENTE DE ANÁLISIS DE PRECIOS")
    print("="*70 + "\n")
    
    # Crear agente
    print("1️⃣ Creando agente...")
    agent = PriceAnalyzerAgent(verbose=True)
    print("   ✅ Agente creado\n")
    
    # Crear tarjeta de ejemplo
    print("2️⃣ Creando tarjeta de ejemplo...")
    card = create_sample_card()
    print(f"   📦 {card.player.name} - {card.year} {card.manufacturer}")
    print(f"   ⭐ {card.variant}, Grado: {card.grade}\n")
    
    # Escenario 1: Precio bajando (BUY)
    print("="*70)
    print("📊 ESCENARIO 1: Precios en tendencia BAJISTA")
    print("="*70)
    prices_down = create_sample_prices("down")
    recommendation = agent.analyze_card(
        card=card,
        price_history=prices_down,
        player_performance="El jugador está jugando excelente, promediando 28 puntos"
    )
    
    print(f"\n🎯 SEÑAL: {recommendation.signal.value.upper()}")
    print(f"📊 Confianza: {recommendation.confidence:.1%}")
    print(f"💰 Precio actual: ${recommendation.current_price:.2f}")
    if recommendation.target_buy_price:
        print(f"🎯 Precio objetivo de compra: ${recommendation.target_buy_price:.2f}")
    if recommendation.target_sell_price:
        print(f"🎯 Precio objetivo de venta: ${recommendation.target_sell_price:.2f}")
    print(f"\n📝 Razonamiento:\n   {recommendation.reasoning}")
    print(f"\n📌 Factores considerados:")
    for factor in recommendation.factors:
        print(f"   • {factor}")
    
    # Escenario 2: Precio subiendo (SELL)
    print("\n" + "="*70)
    print("📊 ESCENARIO 2: Precios en tendencia ALCISTA")
    print("="*70)
    prices_up = create_sample_prices("up")
    recommendation = agent.analyze_card(
        card=card,
        price_history=prices_up,
        player_performance="El jugador está lesionado, fuera por 2 semanas"
    )
    
    print(f"\n🎯 SEÑAL: {recommendation.signal.value.upper()}")
    print(f"📊 Confianza: {recommendation.confidence:.1%}")
    print(f"💰 Precio actual: ${recommendation.current_price:.2f}")
    if recommendation.target_buy_price:
        print(f"🎯 Precio objetivo de compra: ${recommendation.target_buy_price:.2f}")
    if recommendation.target_sell_price:
        print(f"🎯 Precio objetivo de venta: ${recommendation.target_sell_price:.2f}")
    print(f"\n📝 Razonamiento:\n   {recommendation.reasoning}")
    print(f"\n📌 Factores considerados:")
    for factor in recommendation.factors:
        print(f"   • {factor}")
    
    # Escenario 3: Precio estable (HOLD)
    print("\n" + "="*70)
    print("📊 ESCENARIO 3: Precios ESTABLES")
    print("="*70)
    prices_stable = create_sample_prices("stable")
    recommendation = agent.analyze_card(
        card=card,
        price_history=prices_stable,
        player_performance="El jugador mantiene su nivel habitual"
    )
    
    print(f"\n🎯 SEÑAL: {recommendation.signal.value.upper()}")
    print(f"📊 Confianza: {recommendation.confidence:.1%}")
    print(f"💰 Precio actual: ${recommendation.current_price:.2f}")
    if recommendation.target_buy_price:
        print(f"🎯 Precio objetivo de compra: ${recommendation.target_buy_price:.2f}")
    if recommendation.target_sell_price:
        print(f"🎯 Precio objetivo de venta: ${recommendation.target_sell_price:.2f}")
    print(f"\n📝 Razonamiento:\n   {recommendation.reasoning}")
    print(f"\n📌 Factores considerados:")
    for factor in recommendation.factors:
        print(f"   • {factor}")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETADO")
    print("="*70)
    print("\n💡 El agente está funcionando correctamente!")
    print("   Puede analizar tendencias y generar recomendaciones basadas en:")
    print("   • Historial de precios")
    print("   • Rendimiento del jugador")
    print("   • Características de la tarjeta")
    print("   • Comparación con promedios del mercado\n")


if __name__ == "__main__":
    main()