"""
MLB Stats Tool - Enhanced with official MLB Stats API
"""

from typing import Dict, Any
import httpx
from src.utils.stats_cache import stats_cache
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class MLBStatsTool:
    """Enhanced MLB stats tool with official MLB API"""

    def __init__(self):
        self.name = "MLB Stats Tool (Official API)"
        self.base_url = "https://statsapi.mlb.com/api/v1"

    async def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """
        Get real MLB player statistics from official API

        Args:
            player_name: Player's name

        Returns:
            Dict with player statistics
        """
        # Check cache first
        cached = stats_cache.get("player_stats", f"mlb_{player_name}")
        if cached:
            cached["from_cache"] = True
            return cached

        try:
            # Search for player
            player_id = await self._search_player(player_name)

            if not player_id:
                return self._get_simulated_stats(player_name)

            # Get player stats
            stats = await self._fetch_player_stats(player_id, player_name)

            if stats and stats.get("success"):
                stats_cache.set("player_stats", f"mlb_{player_name}", stats)
                return stats

            return self._get_simulated_stats(player_name)

        except Exception as e:
            logger.error(f"Error fetching MLB stats for {player_name}: {e}")
            return self._get_simulated_stats(player_name)

    async def _search_player(self, player_name: str) -> int:
        """Search for player by name"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Use sports/players/search endpoint
                response = await client.get(
                    f"{self.base_url}/sports/1/players", params={"season": 2025}
                )

                if response.status_code == 200:
                    data = response.json()
                    players = data.get("people", [])

                    # Find matching player
                    for player in players:
                        full_name = player.get("fullName", "")
                        if player_name.lower() in full_name.lower():
                            return player.get("id")

            return None

        except Exception as e:
            logger.error(f"Error searching MLB player: {e}")
            return None

    async def _fetch_player_stats(
        self, player_id: int, player_name: str
    ) -> Dict[str, Any]:
        """Fetch detailed player stats"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/people/{player_id}/stats",
                    params={"stats": "season", "season": 2025, "group": "hitting"},
                )

                if response.status_code == 200:
                    data = response.json()
                    stats_data = data.get("stats", [])

                    if stats_data and stats_data[0].get("splits"):
                        split = stats_data[0]["splits"][0]
                        stat = split.get("stat", {})

                        return {
                            "success": True,
                            "simulated": False,
                            "player_name": player_name,
                            "note": "Real data from MLB Stats API",
                            "batting_avg": float(stat.get("avg", 0)),
                            "home_runs": int(stat.get("homeRuns", 0)),
                            "rbi": int(stat.get("rbi", 0)),
                            "hits": int(stat.get("hits", 0)),
                            "runs": int(stat.get("runs", 0)),
                            "stolen_bases": int(stat.get("stolenBases", 0)),
                        }

            return {"success": False}

        except Exception as e:
            logger.error(f"Error fetching MLB player stats: {e}")
            return {"success": False}

    def _get_simulated_stats(self, player_name: str) -> Dict[str, Any]:
        """Return simulated stats as fallback"""
        return {
            "success": True,
            "simulated": True,
            "player_name": player_name,
            "note": "Using simulated data - Player not found in API",
            "batting_avg": 0.285,
            "home_runs": 28,
            "rbi": 95,
            "hits": 165,
            "runs": 88,
            "stolen_bases": 12,
        }
