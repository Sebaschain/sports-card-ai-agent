"""
NBA Stats Tool - Enhanced with real NBA API
Uses nba_api (official NBA.com API) with fallbacks
"""

from typing import Dict, Any, Optional
import httpx
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo, playergamelog
from nba_api.stats.static import players
from src.utils.stats_cache import stats_cache


class NBAStatsTool:
    """Enhanced NBA stats tool with real API integration"""

    def __init__(self):
        self.name = "NBA Stats Tool (Real API)"
        self.current_season = "2024-25"

    async def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """
        Get real NBA player statistics

        Args:
            player_name: Player's name

        Returns:
            Dict with player statistics
        """
        # Check cache first
        cached = stats_cache.get("player_stats", f"nba_{player_name}")
        if cached:
            cached["from_cache"] = True
            return cached

        try:
            # Find player by name
            player_dict = players.find_players_by_full_name(player_name)

            if not player_dict:
                # Try partial match
                all_players = players.get_active_players()
                player_dict = [
                    p
                    for p in all_players
                    if player_name.lower() in p["full_name"].lower()
                ]

            if not player_dict:
                return {
                    "success": False,
                    "error": f"Player '{player_name}' not found",
                    "simulated": False,
                }

            player = player_dict[0]
            player_id = player["id"]

            # Get career stats
            career = playercareerstats.PlayerCareerStats(player_id=player_id)
            career_df = career.get_data_frames()[0]

            # Get current season stats (most recent)
            if not career_df.empty:
                latest_season = career_df.iloc[-1]

                games_played = int(latest_season["GP"])
                points = float(latest_season["PTS"])
                assists = float(latest_season["AST"])
                rebounds = float(latest_season["REB"])

                ppg = points / games_played if games_played > 0 else 0
                apg = assists / games_played if games_played > 0 else 0
                rpg = rebounds / games_played if games_played > 0 else 0

                result = {
                    "success": True,
                    "simulated": False,
                    "player_name": player["full_name"],
                    "player_id": player_id,
                    "season": str(latest_season["SEASON_ID"]),
                    "team": latest_season["TEAM_ABBREVIATION"],
                    "games_played": games_played,
                    "points_per_game": round(ppg, 1),
                    "assists_per_game": round(apg, 1),
                    "rebounds_per_game": round(rpg, 1),
                    "field_goal_pct": round(float(latest_season["FG_PCT"]) * 100, 1)
                    if latest_season["FG_PCT"]
                    else 0,
                    "three_point_pct": round(float(latest_season["FG3_PCT"]) * 100, 1)
                    if latest_season["FG3_PCT"]
                    else 0,
                    "free_throw_pct": round(float(latest_season["FT_PCT"]) * 100, 1)
                    if latest_season["FT_PCT"]
                    else 0,
                    "note": "Real data from NBA.com API",
                }

                # Cache the result
                stats_cache.set("player_stats", f"nba_{player_name}", result)
                return result

            return {"success": False, "error": "No stats available", "simulated": False}

        except Exception as e:
            print(f"Error fetching NBA stats for {player_name}: {e}")
            # Return simulated data as fallback
            return {
                "success": True,
                "simulated": True,
                "player_name": player_name,
                "note": f"Using simulated data - API error: {str(e)}",
                "games_played": 65,
                "points_per_game": 24.5,
                "assists_per_game": 6.8,
                "rebounds_per_game": 7.2,
                "field_goal_pct": 48.5,
                "three_point_pct": 36.2,
                "free_throw_pct": 85.0,
            }
