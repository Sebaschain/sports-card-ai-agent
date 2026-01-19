"""
MLB Statistics Tool
Get real player stats from MLB Stats API
"""
from typing import Dict, Any, Optional

try:
    import statsapi
    MLB_API_AVAILABLE = True
except ImportError:
    MLB_API_AVAILABLE = False


class MLBStatsTool:
    """Tool to fetch real MLB player statistics"""
    
    def __init__(self):
        self.name = "MLB Stats Tool"
        if not MLB_API_AVAILABLE:
            print("⚠️  MLB Stats API not installed. Using simulated data.")
    
    def find_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Find player by name"""
        if not MLB_API_AVAILABLE:
            return None
        
        try:
            # Search for player
            results = statsapi.lookup_player(player_name)
            if results:
                return results[0]
            return None
        except Exception as e:
            print(f"Error finding player: {e}")
            return None
    
    def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """
        Get current season stats for a player
        
        Returns:
            Dict with player stats
        """
        if not MLB_API_AVAILABLE:
            return self._get_simulated_stats(player_name)
        
        try:
            # Find player
            player = self.find_player(player_name)
            if not player:
                return {
                    "success": False,
                    "error": f"Player '{player_name}' not found"
                }
            
            player_id = player['id']
            
            # Get stats for current season
            stats = statsapi.player_stat_data(
                player_id, 
                group="hitting",  # or "pitching"
                type="season"
            )
            
            if stats and 'stats' in stats:
                current_stats = stats['stats'][0]['stats']
                
                return {
                    "success": True,
                    "player_name": player_name,
                    "player_id": player_id,
                    "team": stats.get('current_team', 'Unknown'),
                    "position": stats.get('position', 'Unknown'),
                    "season": "2024",
                    "games_played": current_stats.get('gamesPlayed', 0),
                    "batting_avg": float(current_stats.get('avg', 0)),
                    "home_runs": int(current_stats.get('homeRuns', 0)),
                    "rbi": int(current_stats.get('rbi', 0)),
                    "hits": int(current_stats.get('hits', 0)),
                }
            else:
                return {
                    "success": False,
                    "error": "No stats available"
                }
        
        except Exception as e:
            print(f"Error fetching MLB stats: {e}")
            return self._get_simulated_stats(player_name)
    
    def _get_simulated_stats(self, player_name: str) -> Dict[str, Any]:
        """Simulated stats when API is not available"""
        return {
            "success": True,
            "player_name": player_name,
            "simulated": True,
            "team": "Unknown",
            "position": "Unknown",
            "season": "2024",
            "games_played": 120,
            "batting_avg": 0.285,
            "home_runs": 28,
            "rbi": 85,
            "hits": 135,
            "note": "Simulated data - install mlb-statsapi for real stats"
        }