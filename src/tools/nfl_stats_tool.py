"""
NFL Stats Tool - Enhanced with ESPN API and web scraping
"""

from typing import Dict, Any, Optional
import httpx
import asyncio
from src.utils.stats_cache import stats_cache


class NFLStatsTool:
    """Enhanced NFL stats tool with real data sources"""

    def __init__(self):
        self.name = "NFL Stats Tool (Real Data)"
        self.espn_base = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.espn_common = (
            "https://site.web.api.espn.com/apis/common/v3/sports/football/nfl"
        )
        # Simple in-memory cache for player name -> ID mapping to avoid expensive searches
        self.player_id_cache = {}

    async def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """
        Get real NFL player statistics

        Args:
            player_name: Player's name

        Returns:
            Dict with player statistics
        """
        # Check cache first
        cache_key = f"nfl_{player_name.lower().replace(' ', '_')}"
        cached = stats_cache.get("player_stats", cache_key)
        if cached:
            cached["from_cache"] = True
            return cached

        try:
            # Try ESPN API
            stats = await self._fetch_from_espn(player_name)
            if stats and stats.get("success"):
                stats_cache.set("player_stats", cache_key, stats)
                return stats

            # Fallback to simulated data
            print(f"ESPN API failed for {player_name}, using simulated data.")
            return self._get_simulated_stats(player_name)

        except Exception as e:
            print(f"Error fetching NFL stats for {player_name}: {e}")
            return self._get_simulated_stats(player_name)

    async def _fetch_from_espn(self, player_name: str) -> Dict[str, Any]:
        """Fetch stats from ESPN API"""
        async with httpx.AsyncClient(timeout=20.0) as client:
            player_id = await self._find_player_id(client, player_name)

            if not player_id:
                return {"success": False, "error": "Player not found"}

            return await self._get_stats_from_id(client, player_id, player_name)

    async def _find_player_id(
        self, client: httpx.AsyncClient, player_name: str
    ) -> Optional[str]:
        """Find player ID by name, checking cache then searching teams"""
        normalized_name = player_name.lower()

        # 1. Check local ID cache
        if normalized_name in self.player_id_cache:
            return self.player_id_cache[normalized_name]

        print(f"Searching ESPN for {player_name} (this may take a moment)...")

        # 2. Search via Team Rosters (Most reliable from debug testing)
        teams_url = f"{self.espn_base}/teams"
        try:
            resp = await client.get(teams_url)
            data = resp.json()

            # Helper to fetch roster and search
            async def check_team_roster(team_item):
                team_id = team_item.get("team", {}).get("id")
                if not team_id:
                    return None

                try:
                    roster_url = f"{self.espn_base}/teams/{team_id}/roster"
                    r_resp = await client.get(roster_url)
                    r_data = r_resp.json()

                    if "athletes" in r_data:
                        for section in r_data["athletes"]:
                            for item in section.get("items", []):
                                if (
                                    player_name.lower()
                                    in item.get("displayName", "").lower()
                                ):
                                    return item
                except Exception:
                    pass
                return None

            # Gather all teams
            if "sports" in data:
                all_teams = data["sports"][0].get("leagues", [{}])[0].get("teams", [])

                # Run roster checks in parallel batches to avoid timeout but be fast
                # Processing 32 teams is fine in parallel
                roster_tasks = [check_team_roster(team) for team in all_teams]
                results = await asyncio.gather(*roster_tasks)

                for res in results:
                    if res:
                        pid = res.get("id")
                        self.player_id_cache[normalized_name] = pid
                        return pid

        except Exception as e:
            print(f"Error searching teams: {e}")

        return None

    async def _get_stats_from_id(
        self, client: httpx.AsyncClient, player_id: str, player_name: str
    ) -> Dict[str, Any]:
        """Fetch detailed stats using player ID"""
        url = f"{self.espn_common}/athletes/{player_id}/overview"
        try:
            resp = await client.get(url)
            data = resp.json()

            # Initialize result
            result = {
                "success": True,
                "simulated": False,
                "player_name": player_name,  # We could use data['player']['displayName'] if available
                "provider": "ESPN",
                "season": "Current",  # Could extract from response
                "stats": {},
            }

            # Extract Main Statistics
            # The structure is data['statistics']['categories']...

            stats_root = data.get("statistics", {})

            # Flatten the stats for easier consumption
            # We want key stats like Passing Yards, TDs, etc.

            # The API returns specific categories (passing, rushing, etc.)
            # We will grab the "Regular Season" split usually

            splits = stats_root.get("splits", [])
            reg_season = next(
                (s for s in splits if s.get("displayName") == "Regular Season"), None
            )

            if reg_season:
                stat_values = reg_season.get("stats", [])
                labels = stats_root.get(
                    "names", []
                )  # e.g. ['completions', 'passingYards'...]

                # Map them
                extracted_stats = {}
                for i, label in enumerate(labels):
                    if i < len(stat_values):
                        # Clean values (remove commas)
                        val = stat_values[i].replace(",", "")
                        try:
                            if "." in val:
                                extracted_stats[label] = float(val)
                            else:
                                extracted_stats[label] = int(val)
                        except Exception:
                            extracted_stats[label] = val

                # Normalize common fields for the agent
                result.update(
                    {
                        "passing_yards": extracted_stats.get("passingYards", 0),
                        "passing_touchdowns": extracted_stats.get(
                            "passingTouchdowns", 0
                        ),
                        "interceptions": extracted_stats.get("interceptions", 0),
                        "rushing_yards": extracted_stats.get("rushingYards", 0),
                        "rushing_touchdowns": extracted_stats.get(
                            "rushingTouchdowns", 0
                        ),
                        "receptions": extracted_stats.get("receptions", 0),
                        "receiving_yards": extracted_stats.get("receivingYards", 0),
                        "receiving_touchdowns": extracted_stats.get(
                            "receivingTouchdowns", 0
                        ),
                    }
                )

                # Add raw for detail
                result["raw_stats"] = extracted_stats

            return result

        except Exception as e:
            print(f"Error parsing detailed stats: {e}")
            return {"success": False, "error": f"Stats parsing error: {str(e)}"}

    def _get_simulated_stats(self, player_name: str) -> Dict[str, Any]:
        """Return simulated stats as fallback"""
        return {
            "success": True,
            "simulated": True,
            "player_name": player_name,
            "note": "Using simulated data - Real API integration in progress",
            "passing_yards": 3500,
            "touchdowns": 28,
            "interceptions": 10,
            "completion_percentage": 65.5,
            "rushing_yards": 250,
            "receptions": 0,
            "receiving_yards": 0,
            "receiving_touchdowns": 0,
        }
