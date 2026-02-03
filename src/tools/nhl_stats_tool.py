from typing import Dict, Any, Optional
import asyncio
import requests
from src.tools.base_tool import BaseStatsTool


class NHLStatsTool(BaseStatsTool):
    """Tool to fetch real NHL player statistics"""

    def __init__(self):
        self._name = "NHL Stats Tool"
        self.base_url = "https://api-web.nhle.com/v1"

    @property
    def tool_name(self) -> str:
        return self._name

    def find_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Find player by name using NHL API search
        Note: NHL API doesn't have a direct search, so we use a workaround
        """
        # For now, return None - would need player ID mapping
        return None

    async def get_player_stats(
        self, player_name: str, player_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get current season stats for a player

        Args:
            player_name: Player name
            player_id: NHL player ID (if known)

        Returns:
            Dict with player stats
        """
        if not player_id:
            # Common NHL stars IDs (for demo)
            player_ids = {
                "connor mcdavid": 8478402,
                "auston matthews": 8479318,
                "nathan mackinnon": 8477492,
                "leon draisaitl": 8477934,
                "sidney crosby": 8471675,
            }
            player_id = player_ids.get(player_name.lower())

        if not player_id:
            return self._get_simulated_stats(player_name)

        try:
            # Get player info
            url = f"{self.base_url}/player/{player_id}/landing"
            # Use asyncio.to_thread for requests
            response = await asyncio.to_thread(requests.get, url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Extract current season stats
                current_season = (
                    data.get("featuredStats", {})
                    .get("regularSeason", {})
                    .get("subSeason", {})
                )

                return {
                    "success": True,
                    "player_name": player_name,
                    "player_id": player_id,
                    "team": data.get("currentTeamAbbrev", "Unknown"),
                    "position": data.get("position", "Unknown"),
                    "season": current_season.get("season", "2024-25"),
                    "games_played": current_season.get("gamesPlayed", 0),
                    "goals": current_season.get("goals", 0),
                    "assists": current_season.get("assists", 0),
                    "points": current_season.get("points", 0),
                    "points_per_game": current_season.get("points", 0)
                    / max(current_season.get("gamesPlayed", 1), 1),
                }
            else:
                return self._get_simulated_stats(player_name)

        except Exception as e:
            print(f"Error fetching NHL stats: {e}")
            return self._get_simulated_stats(player_name)

    def _get_simulated_stats(self, player_name: str) -> Dict[str, Any]:
        """Simulated stats when API fails"""
        return {
            "success": True,
            "player_name": player_name,
            "simulated": True,
            "team": "Unknown",
            "position": "Unknown",
            "season": "2024-25",
            "games_played": 50,
            "goals": 35,
            "assists": 40,
            "points": 75,
            "points_per_game": 1.5,
            "note": "Simulated data - real API requires player ID",
        }
