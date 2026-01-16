"""View saved analyses from database"""
from src.utils.database import get_db
from src.utils.repository import CardRepository

with get_db() as db:
    print("\n" + "="*70)
    print("📊 ANÁLISIS GUARDADOS EN BASE DE DATOS")
    print("="*70 + "\n")
    
    analyses = CardRepository.get_all_analyses(db, limit=10)
    
    if not analyses:
        print("⚠️  No hay análisis guardados todavía")
    else:
        for i, analysis in enumerate(analyses, 1):
            print(f"{i}. {analysis['player_name']} - {analysis['year']} {analysis['manufacturer']}")
            print(f"   🎯 Señal: {analysis['signal']}")
            print(f"   📊 Confianza: {analysis['confidence']:.0%}")
            print(f"   💰 Precio: ${analysis['current_price']:.2f}" if analysis['current_price'] else "")
            print(f"   📅 Fecha: {analysis['timestamp'].strftime('%Y-%m-%d %H:%M')}")
            print()
    
    stats = CardRepository.get_statistics(db)
    print("="*70)
    print("📈 ESTADÍSTICAS")
    print("="*70)
    print(f"Jugadores: {stats['total_players']}")
    print(f"Tarjetas: {stats['total_cards']}")
    print(f"Análisis: {stats['total_analyses']}")
    print(f"Precios: {stats['total_prices']}")
    print("\n" + "="*70)