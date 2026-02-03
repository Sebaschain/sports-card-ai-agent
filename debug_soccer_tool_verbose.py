import asyncio
from src.tools.soccer_stats_tool import SoccerStatsTool
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG)


async def debug_soccer():
    print("Initializing SoccerStatsTool...")
    tool = SoccerStatsTool()

    # Test Erling Haaland (EPL)
    print("\n--- Testing Erling Haaland ---")
    stats = await tool.get_player_stats("Erling Haaland")
    print(f"Result: {stats}")

    # Test Lionel Messi (MLS)
    print("\n--- Testing Lionel Messi ---")
    stats = await tool.get_player_stats("Lionel Messi")
    print(f"Result: {stats}")


if __name__ == "__main__":
    asyncio.run(debug_soccer())
