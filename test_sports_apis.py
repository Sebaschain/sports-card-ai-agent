"""
Test script for real-time sports data APIs
"""

import asyncio
import logging
from src.tools.nba_stats_tool import NBAStatsTool
from src.tools.nfl_stats_tool import NFLStatsTool
from src.tools.mlb_stats_tool import MLBStatsTool
from src.tools.nhl_stats_tool import NHLStatsTool
from src.tools.soccer_stats_tool import SoccerStatsTool

# Configure logging
logging.basicConfig(level=logging.DEBUG)


async def test_all_sports():
    """Test all sports stats tools"""

    print("=" * 70)
    print("TESTING REAL-TIME SPORTS DATA APIS")
    print("=" * 70)

    # Test NBA
    # print("\n1. Testing NBA (LeBron James)...")
    # nba_tool = NBAStatsTool()
    # nba_stats = await nba_tool.get_player_stats("LeBron James")
    # print(f"   Success: {nba_stats.get('success')}")
    # print(f"   Simulated: {nba_stats.get('simulated')}")
    # print(f"   PPG: {nba_stats.get('points_per_game')}")
    # print(f"   Note: {nba_stats.get('note')}")

    # Test NFL
    # print("\n2. Testing NFL (Patrick Mahomes)...")
    # nfl_tool = NFLStatsTool()
    # nfl_stats = await nfl_tool.get_player_stats("Patrick Mahomes")
    # print(f"   Success: {nfl_stats.get('success')}")
    # print(f"   Simulated: {nfl_stats.get('simulated')}")
    # print(f"   Passing Yards: {nfl_stats.get('passing_yards')}")
    # print(f"   Note: {nfl_stats.get('note')}")

    # Test MLB
    # print("\n3. Testing MLB (Shohei Ohtani)...")
    # mlb_tool = MLBStatsTool()
    # mlb_stats = await mlb_tool.get_player_stats("Shohei Ohtani")
    # print(f"   Success: {mlb_stats.get('success')}")
    # print(f"   Simulated: {mlb_stats.get('simulated')}")
    # print(f"   Batting Avg: {mlb_stats.get('batting_avg')}")
    # print(f"   Note: {mlb_stats.get('note')}")

    # Test NHL
    # print("\n4. Testing NHL (Connor McDavid)...")
    # nhl_tool = NHLStatsTool()
    # nhl_stats = await nhl_tool.get_player_stats("Connor McDavid")
    # print(f"   Success: {nhl_stats.get('success')}")
    # print(f"   Simulated: {nhl_stats.get('simulated')}")
    # print(f"   Points: {nhl_stats.get('points')}")
    # print(f"   Note: {nhl_stats.get('note')}")

    # Test Soccer
    # Test Soccer
    print("\n5. Testing Soccer (Erling Haaland)...")
    soccer_tool = SoccerStatsTool()
    soccer_stats = await soccer_tool.get_player_stats("Erling Haaland")
    print(f"   Success: {soccer_stats.get('success')}")
    print(f"   Simulated: {soccer_stats.get('simulated')}")
    print(f"   Goals: {soccer_stats.get('goals')}")
    print(f"   Note: {soccer_stats.get('note')}")

    print("\n" + "=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_all_sports())
