import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from src.agents.supervisor_agent import SupervisorAgent


async def test_phase3():
    print("🚀 Testing Phase 3: Advanced Data Integration...")
    supervisor = SupervisorAgent()

    # Test with an NBA player to trigger the multi-provider logic (NBA API -> Ball Don't Lie)
    player = "Nikola Jokic"
    print(f"\n🔍 Analyzing {player} (NBA)...")

    result = await supervisor.analyze_investment_opportunity(
        player_name=player, year=2015, manufacturer="Panini", sport="NBA"
    )

    print("\n✅ Analysis Complete!")
    rec = result["recommendation"]
    detailed = result["detailed_analysis"]

    print(f"Signal: {rec['signal']} (Confidence: {rec['confidence']:.2%})")

    player_data = detailed["player"]["real_stats"]
    print(f"\n📊 Player Stats Source: {player_data.get('source', 'Unknown')}")
    print(f" - PPG: {player_data.get('points_per_game', 0)}")
    print(f" - APG: {player_data.get('assists_per_game', 0)}")

    news = detailed["player"]["news"]
    print(f"\n🗞️ News Count: {news.get('news_count', 0)}")
    if news.get("news"):
        print(f" - Latest: {news['news'][0]['title']}")

    sentiment = detailed["player"]["sentiment"]
    if sentiment:
        print(f"\n😊 Sentiment: {sentiment.get('overall_sentiment', 'Unknown')}")


if __name__ == "__main__":
    asyncio.run(test_phase3())
