"""
Soccer Stats Tool - Enhanced with Football-Data.org API and ESPN Scraping
"""

from typing import Dict, Any, Optional
import httpx
import asyncio
from src.utils.stats_cache import stats_cache
from src.utils.scraping_utils import scraper
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class SoccerStatsTool:
    """Enhanced Soccer stats tool with real API and scraping fallback"""

    def __init__(self):
        self.name = "Soccer Stats Tool (Real Data)"
        # Football-Data.org API
        self.api_base = "https://api.football-data.org/v4"
        self.api_key = None  # Set via environment variable in production

        # ESPN Scraping Fallback
        self.espn_base = "https://site.api.espn.com/apis/site/v2/sports/soccer"
        self.espn_common = "https://site.web.api.espn.com/apis/common/v3/sports/soccer"
        self.leagues = [
            "eng.1",
            "esp.1",
            "fra.1",
            "ger.1",
            "ita.1",
            "usa.1",
            "uefa.champions",
        ]

        # Simple in-memory cache for player name -> ID mapping
        self.player_id_cache = {}

    async def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """
        Get real Soccer player statistics

        Args:
            player_name: Player's name

        Returns:
            Dict with player statistics
        """
        # Check cache first
        cache_key = f"soccer_{player_name.lower().replace(' ', '_')}"
        cached = stats_cache.get("player_stats", cache_key)
        if cached:
            cached["from_cache"] = True
            return cached

        try:
            # 1. Try API if key available (Placeholder for future)
            if self.api_key:
                stats = await self._fetch_from_api(player_name)
                if stats and stats.get("success"):
                    stats_cache.set("player_stats", cache_key, stats)
                    return stats

            # 2. Try ESPN Scraping Fallback
            stats = await self._fetch_from_espn_scraping(player_name)
            if stats and stats.get("success"):
                stats_cache.set("player_stats", cache_key, stats)
                return stats

            # 3. Fallback to simulated data
            # print(f"Data sources failed for {player_name}, using simulated data.")
            return self._get_simulated_stats(player_name)

        except Exception as e:
            logger.error(f"Error fetching Soccer stats for {player_name}: {e}")
            return self._get_simulated_stats(player_name)

    async def _fetch_from_espn_scraping(self, player_name: str) -> Dict[str, Any]:
        """Fetch stats by scraping ESPN internal APIs"""
        # Use headers to avoid bot detection
        headers = scraper.get_headers()
        async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
            player_info = await self._find_player_id(client, player_name)

            if not player_info:
                return {"success": False, "error": "Player not found"}

            return await self._get_stats_from_id(
                client, player_info["id"], player_info["league"], player_name
            )

    async def _find_player_id(
        self, client: httpx.AsyncClient, player_name: str
    ) -> Optional[Dict[str, str]]:
        """Find player ID and League by name"""
        normalized_name = player_name.lower()

        # 1. Check local ID cache
        if normalized_name in self.player_id_cache:
            return self.player_id_cache[normalized_name]

        logger.info(
            f"Searching ESPN Soccer for {player_name} (checking major leagues)..."
        )

        # 2. Search via Team Rosters
        # Logic similar to debug script: iterate leagues -> teams -> roster

        for league in self.leagues:
            teams_url = f"{self.espn_base}/{league}/teams"
            try:
                resp = await client.get(teams_url)
                data = resp.json()

                if "sports" not in data:
                    continue

                teams = data["sports"][0].get("leagues", [{}])[0].get("teams", [])

                # We can construct tasks to check rosters in parallel for this league
                # Increasing concurrency for speed
                semaphore = asyncio.Semaphore(5)

                async def check_roster(team_item, lg):
                    async with semaphore:
                        tid = team_item.get("team", {}).get("id")
                        if not tid:
                            return None
                        try:
                            roster_url = f"{self.espn_base}/{lg}/teams/{tid}/roster"
                            # print(f"Checking roster: {roster_url}") # Debug
                            r_resp = await client.get(roster_url)

                            if r_resp.status_code != 200:
                                logger.warning(
                                    f"Failed to fetch roster {tid}: {r_resp.status_code}"
                                )
                                return None

                            r_data = r_resp.json()
                            if "athletes" in r_data:
                                for grp in r_data["athletes"]:
                                    for ath in grp.get("items", []):
                                        name = ath.get("displayName", "")
                                        if player_name.lower() in name.lower():
                                            logger.info(
                                                f"FOUND PLAYER: {name} in {lg} team {tid}"
                                            )
                                            return {"id": ath.get("id"), "league": lg}
                        except Exception as e:
                            logger.error(f"Error checking roster {tid}: {e}")
                            pass

                        # Small delay to be nice
                        await asyncio.sleep(0.1)
                        return None

                # Batch requests for speed
                roster_tasks = [check_roster(t, league) for t in teams]
                results = await asyncio.gather(*roster_tasks)

                for res in results:
                    if res:
                        self.player_id_cache[normalized_name] = res
                        return res

            except Exception as e:
                logger.error(f"Error searching league {league}: {e}")

        return None

    async def _get_stats_from_id(
        self, client: httpx.AsyncClient, player_id: str, league: str, player_name: str
    ) -> Dict[str, Any]:
        """Fetch detailed stats using player ID"""
        url = f"{self.espn_common}/{league}/athletes/{player_id}/overview"
        try:
            resp = await client.get(url)
            data = resp.json()

            result = {
                "success": True,
                "simulated": False,
                "player_name": player_name,
                "provider": "ESPN Scraping",
                "stats": {},
                "league": league,
            }

            # Parsing ESPN Soccer Stats Structure
            # Usually data['statistics']['splits'] contains 'General' or specific competitions

            stats_root = data.get("statistics", {})
            splits = stats_root.get("splits", [])

            # Try to find a summary or total split
            # Often the first one or one named "Total" or valid competition name
            # We'll take the first non-empty one that looks like stats

            target_split = None
            if splits:
                target_split = splits[
                    0
                ]  # Default to first (usually current season/comp)

            if target_split:
                stats = target_split.get("stats", [])
                labels = stats_root.get("names", [])

                extracted = {}
                for i, label in enumerate(labels):
                    if i < len(stats):
                        val = stats[i]
                        try:
                            extracted[label] = float(val) if "." in val else int(val)
                        except Exception:
                            extracted[label] = val

                # Normalize common soccer stats
                result.update(
                    {
                        "goals": extracted.get("goals", 0),
                        "assists": extracted.get("assists", 0),
                        "matches_played": extracted.get("appearances", 0)
                        or extracted.get("gamesPlayed", 0),
                        "minutes_played": extracted.get("minutes", 0),
                        "yellow_cards": extracted.get("yellowCards", 0),
                        "red_cards": extracted.get("redCards", 0),
                        "shots": extracted.get("shots", 0),
                        "shots_on_target": extracted.get("shotsOnGoal", 0),
                    }
                )

                # Calculate calculated fields
                matches = result["matches_played"]
                if matches > 0:
                    result["goals_per_game"] = round(result["goals"] / matches, 2)
                else:
                    result["goals_per_game"] = 0.0

            return result

        except Exception as e:
            logger.error(f"Error parsing soccer stats: {e}")
            return {"success": False, "error": str(e)}

    async def _fetch_from_api(self, player_name: str) -> Dict[str, Any]:
        """Fetch stats from Football-Data.org API (Placeholder)"""
        # ... logic would go here if we had API key ...
        return {"success": False}

    def _get_simulated_stats(self, player_name: str) -> Dict[str, Any]:
        """Return simulated stats as fallback"""
        import random

        random.seed(player_name)

        goals = random.randint(5, 30)
        assists = random.randint(2, 15)
        matches = random.randint(20, 38)

        return {
            "success": True,
            "simulated": True,
            "player_name": player_name,
            "note": "Using simulated data - Real stats unavailable",
            "goals": goals,
            "assists": assists,
            "matches_played": matches,
            "minutes_played": matches * 85,
            "yellow_cards": random.randint(0, 5),
            "red_cards": 0,
            "goals_per_game": round(goals / matches, 2),
        }
