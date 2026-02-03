import asyncio
from src.tools.nfl_stats_tool import NFLStatsTool
from src.agents.player_analysis_agent import PlayerAnalysisAgent


async def test_nfl_deep_dive():
    print("=" * 70)
    print("TESTING NFL DEEP DIVE INTEGRATION")
    print("=" * 70)

    players = [
        ("Patrick Mahomes", "QB"),
        ("Christian McCaffrey", "RB"),
        ("Justin Jefferson", "WR"),
    ]

    agent = PlayerAnalysisAgent()
    # Ensure tool is fresh
    agent.nfl_tool = NFLStatsTool()

    for name, pos in players:
        print(f"\n--- Analyzing {name} ({pos}) ---")

        # 1. Get raw stats
        print(f"Fetching stats for {name}...")
        stats = await agent.nfl_tool.get_player_stats(name)

        if not stats.get("success"):
            print(f"FAILED to get stats: {stats.get('error')}")
            continue

        print(f"Stats Provider: {stats.get('provider', 'Simulated')}")
        print(f"Real Data: {not stats.get('simulated')}")

        # Print key stats found
        keys = [
            "passing_yards",
            "passing_touchdowns",
            "rushing_yards",
            "rushing_touchdowns",
            "receiving_yards",
            "receptions",
        ]
        found_stats = {k: stats.get(k) for k in keys if stats.get(k)}
        print(f"Key Stats: {found_stats}")

        # 2. Analyze with Agent
        print(f"Running Agent Analysis...")
        analysis = await agent.analyze_player(name, "NFL")

        score_data = analysis["analysis"]["performance_score"]
        print(f"Score: {score_data['overall_score']}")
        print(f"Rating: {score_data['rating']}")
        print(f"Trend: {score_data['trend']}")
        print(f"Risk: {analysis['analysis']['risk_assessment']['risk_level']}")


if __name__ == "__main__":
    asyncio.run(test_nfl_deep_dive())
