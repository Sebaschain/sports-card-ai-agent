import asyncio
import requests
from typing import Dict, Any
from src.tools.base_tool import BaseStatsTool


class BallDontLieTool(BaseStatsTool):
    """Tool to fetch NBA statistics from Ball Don't Lie API"""

    def __init__(self):
        self._name = "Ball Don't Lie NBA Tool"
        self.base_url = "https://www.balldontlie.io/api/v1"

    @property
    def tool_name(self) -> str:
        return self._name

    async def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """
        Get NBA player stats from Ball Don't Lie
        """
        try:
            # 1. Search for player
            search_url = f"{self.base_url}/players?search={player_name}"
            response = await asyncio.to_thread(requests.get, search_url, timeout=10)

            if response.status_code != 200:
                return {"success": False, "error": f"API Error: {response.status_code}"}

            data = response.json()
            if not data.get("data"):
                return {"success": False, "error": f"Player '{player_name}' not found"}

            player = data["data"][0]
            player_id = player["id"]

            # 2. Get season averages (latest available)
            # Note: Ball Don't Lie usually requires a specific season
            stats_url = f"{self.base_url}/season_averages?player_ids[]={player_id}"
            stats_response = await asyncio.to_thread(
                requests.get, stats_url, timeout=10
            )

            if stats_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Stats API Error: {stats_response.status_code}",
                }

            stats_data = stats_response.json()

            if not stats_data.get("data"):
                return {
                    "success": True,
                    "player_name": f"{player['first_name']} {player['last_name']}",
                    "team": player.get("team", {}).get("full_name", "Unknown"),
                    "position": player.get("position", "Unknown"),
                    "note": "No season averages found for latest season",
                }

            stats = stats_data["data"][0]

            return {
                "success": True,
                "player_name": f"{player['first_name']} {player['last_name']}",
                "player_id": player_id,
                "team": player.get("team", {}).get("full_name", "Unknown"),
                "position": player.get("position", "Unknown"),
                "season": stats.get("season", "Current"),
                "games_played": stats.get("games_played", 0),
                "points_per_game": stats.get("pts", 0),
                "assists_per_game": stats.get("ast", 0),
                "rebounds_per_game": stats.get("reb", 0),
                "field_goal_pct": stats.get("fg_pct", 0),
                "source": "Ball Don't Lie",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
