"""
NHL Stats Tool - Enhanced with official NHL API
"""

from typing import Dict, Any, Optional
import httpx
from src.utils.stats_cache import stats_cache
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class NHLStatsTool:
    """Enhanced NHL stats tool with real API"""

    def __init__(self):
        self.name = "NHL Stats Tool (Official API)"
        self.base_url = "https://api-web.nhle.com/v1"
        self.suggest_url = "https://suggest.svc.nhl.com/svc/suggest/v1/minplayers"

    async def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """
        Get real NHL player statistics

        Args:
            player_name: Player's name

        Returns:
            Dict with player statistics
        """
        # Check cache first
        cache_key = f"nhl_{player_name.lower().replace(' ', '_')}"
        cached = stats_cache.get("player_stats", cache_key)
        if cached:
            cached["from_cache"] = True
            return cached

        try:
            # Search for player to get ID
            player_id = await self._find_player_id(player_name)

            if player_id:
                stats = await self._fetch_player_stats(player_id, player_name)
                if stats and stats.get("success"):
                    stats_cache.set("player_stats", cache_key, stats)
                    return stats

            return self._get_simulated_stats(player_name)

        except Exception as e:
            logger.error(f"Error fetching NHL stats for {player_name}: {e}")
            return self._get_simulated_stats(player_name)

    async def _find_player_id(self, player_name: str) -> Optional[str]:
        """Find player ID using NHL suggest API"""
        try:
            # Format: https://suggest.svc.nhl.com/svc/suggest/v1/minplayers/mcdavid/5
            name_query = player_name.lower().replace(" ", "%20")
            url = f"{self.suggest_url}/{name_query}/5"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    # Response is a list of strings: "ID|LastName|FirstName|...|Team|..."
                    suggestions = data.get("suggestions", [])
                    if suggestions:
                        # Take the first suggested player
                        first_suggestion = suggestions[0]
                        player_id = first_suggestion.split("|")[0]
                        return player_id
            return None
        except Exception as e:
            logger.error(f"NHL Player Search error: {e}")
            return None

    async def _fetch_player_stats(
        self, player_id: str, player_name: str
    ) -> Dict[str, Any]:
        """Fetch player stats from NHL API using landing endpoint"""
        try:
            url = f"{self.base_url}/player/{player_id}/landing"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()

                    # Extract seasonal stats (usually featuredStats or seasonTotals)
                    # For a summary, we look at featuredStats.regularSeason
                    featured = data.get("featuredStats", {}).get("regularSeason", {})

                    if not featured:
                        # Fallback to the latest season in seasonTotals if available
                        totals = data.get("seasonTotals", [])
                        if totals:
                            featured = totals[
                                0
                            ]  # Usually the most recent is first or specific by season

                    return {
                        "success": True,
                        "simulated": False,
                        "player_name": player_name,
                        "player_id": player_id,
                        "team": data.get("currentTeamAbbrev", "N/A"),
                        "position": data.get("position", "N/A"),
                        "goals": featured.get("goals", 0),
                        "assists": featured.get("assists", 0),
                        "points": featured.get("points", 0),
                        "games_played": featured.get("gamesPlayed", 0),
                        "plus_minus": featured.get("plusMinus", 0),
                        "penalty_minutes": featured.get("pim", 0),
                        "points_per_game": round(
                            featured.get("points", 0) / featured.get("gamesPlayed", 1),
                            2,
                        )
                        if featured.get("gamesPlayed", 0) > 0
                        else 0,
                        "season": featured.get("season", "Current"),
                    }
            return {"success": False}

        except Exception as e:
            logger.error(f"NHL API API error: {e}")
            return {"success": False}

    def _get_simulated_stats(self, player_name: str) -> Dict[str, Any]:
        """Return simulated stats as fallback"""
        return {
            "success": True,
            "simulated": True,
            "player_name": player_name,
            "note": "Using simulated data - NHL API connection failed",
            "goals": 35,
            "assists": 45,
            "points": 80,
            "games_played": 75,
            "points_per_game": 1.07,
            "plus_minus": 15,
            "penalty_minutes": 20,
        }
