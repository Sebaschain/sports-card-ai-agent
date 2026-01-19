"""Test de APIs de estadísticas reales"""
from src.agents.player_analysis_agent import PlayerAnalysisAgent

print("="*70)
print("🧪 PROBANDO APIS DE ESTADÍSTICAS REALES")
print("="*70)

agent = PlayerAnalysisAgent()

# Test NBA
print("\n1️⃣ TEST NBA - LeBron James")
print("-"*70)
result = agent.analyze_player("LeBron James", "NBA")
if result['real_stats'].get('success'):
    stats = result['real_stats']
    print(f"✅ Datos obtenidos:")
    print(f"   Team: {stats.get('team')}")
    print(f"   PPG: {stats.get('points_per_game', 0):.1f}")
    print(f"   APG: {stats.get('assists_per_game', 0):.1f}")
    print(f"   RPG: {stats.get('rebounds_per_game', 0):.1f}")
    print(f"\n📊 Análisis:")
    print(f"   Score: {result['analysis']['performance_score']['overall_score']}/100")
    print(f"   Rating: {result['analysis']['performance_score']['rating']}")
else:
    print(f"⚠️  {result['real_stats'].get('error', 'No data')}")

# Test NHL
print("\n2️⃣ TEST NHL - Connor McDavid")
print("-"*70)
result = agent.analyze_player("Connor McDavid", "NHL")
if result['real_stats'].get('success'):
    stats = result['real_stats']
    print(f"✅ Datos obtenidos:")
    print(f"   Team: {stats.get('team')}")
    print(f"   Goals: {stats.get('goals', 0)}")
    print(f"   Assists: {stats.get('assists', 0)}")
    print(f"   Points/Game: {stats.get('points_per_game', 0):.2f}")
    print(f"\n📊 Análisis:")
    print(f"   Score: {result['analysis']['performance_score']['overall_score']}/100")
    print(f"   Rating: {result['analysis']['performance_score']['rating']}")
else:
    print(f"⚠️  {result['real_stats'].get('error', 'No data')}")

# Test MLB
print("\n3️⃣ TEST MLB - Mike Trout")
print("-"*70)
result = agent.analyze_player("Mike Trout", "MLB")
if result['real_stats'].get('success'):
    stats = result['real_stats']
    print(f"✅ Datos obtenidos:")
    print(f"   Team: {stats.get('team')}")
    print(f"   BA: {stats.get('batting_avg', 0):.3f}")
    print(f"   HR: {stats.get('home_runs', 0)}")
    print(f"   RBI: {stats.get('rbi', 0)}")
    print(f"\n📊 Análisis:")
    print(f"   Score: {result['analysis']['performance_score']['overall_score']}/100")
    print(f"   Rating: {result['analysis']['performance_score']['rating']}")
else:
    print(f"⚠️  {result['real_stats'].get('error', 'No data')}")

print("\n" + "="*70)
print("✅ TEST COMPLETADO")
print("="*70)