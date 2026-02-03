import asyncio
import requests
from typing import Dict, Any
from src.tools.base_tool import BaseStatsTool


from src.utils.config import settings


class BallDontLieTool(BaseStatsTool):
    """Tool to fetch NBA statistics from Ball Don't Lie API (v2)"""

    def __init__(self):
        self._name = "Ball Don't Lie NBA Tool"
        self.base_url = "https://api.balldontlie.io/v1"
        self.api_key = settings.BDL_API_KEY

    @property
    def tool_name(self) -> str:
        return self._name

    async def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """
        Get NBA player stats from Ball Don't Lie
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Ball Don't Lie API Key not configured. Get one at balldontlie.io",
            }

        headers = {"Authorization": self.api_key}

        try:
            # 1. Search for player
            search_url = f"{self.base_url}/players"
            params = {"search": player_name}
            response = await asyncio.to_thread(
                requests.get, search_url, params=params, headers=headers, timeout=10
            )

            if response.status_code == 401:
                return {"success": False, "error": "Invalid Ball Don't Lie API Key"}
            elif response.status_code == 429:
                return {
                    "success": False,
                    "error": "Ball Don't Lie API Rate limit exceeded",
                }
            elif response.status_code != 200:
                return {"success": False, "error": f"API Error: {response.status_code}"}

            data = response.json()
            if not data.get("data"):
                return {"success": False, "error": f"Player '{player_name}' not found"}

            player = data["data"][0]
            player_id = player["id"]

            # 2. Get season averages (latest available)
            # v2 uses 'season' as a required or defaulted param
            stats_url = f"{self.base_url}/season_averages"
            stats_params = {"player_ids[]": player_id}

            stats_response = await asyncio.to_thread(
                requests.get,
                stats_url,
                params=stats_params,
                headers=headers,
                timeout=10,
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
                "source": "Ball Don't Lie (v2)",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
