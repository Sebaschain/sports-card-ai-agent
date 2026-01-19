"""
NBA Statistics Tool
Get real player stats from NBA API
"""
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from nba_api.stats.endpoints import playercareerstats, commonplayerinfo
    from nba_api.stats.static import players
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False


class NBAStatsTool:
    """Tool to fetch real NBA player statistics"""
    
    def __init__(self):
        self.name = "NBA Stats Tool"
        if not NBA_API_AVAILABLE:
            print("⚠️  NBA API not installed. Using simulated data.")
    
    def find_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Find player by name"""
        if not NBA_API_AVAILABLE:
            return None
        
        try:
            player_dict = players.find_players_by_full_name(player_name)
            if player_dict:
                return player_dict[0]
            return None
        except Exception as e:
            print(f"Error finding player: {e}")
            return None
    
    def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """
        Get current season stats for a player
        
        Returns:
            Dict with player stats and performance info
        """
        if not NBA_API_AVAILABLE:
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
            
            # Get career stats
            career = playercareerstats.PlayerCareerStats(player_id=player_id)
            career_df = career.get_data_frames()[0]
            
            # Get current season (latest season)
            if len(career_df) > 0:
                current_season = career_df.iloc[-1]
                
                # Get player info
                info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
                info_df = info.get_data_frames()[0]
                
                return {
                    "success": True,
                    "player_name": player_name,
                    "player_id": player_id,
                    "team": info_df['TEAM_NAME'].iloc[0] if len(info_df) > 0 else "Unknown",
                    "position": info_df['POSITION'].iloc[0] if len(info_df) > 0 else "Unknown",
                    "season": current_season['SEASON_ID'],
                    "games_played": int(current_season['GP']),
                    "points_per_game": float(current_season['PTS']) / float(current_season['GP']) if current_season['GP'] > 0 else 0,
                    "assists_per_game": float(current_season['AST']) / float(current_season['GP']) if current_season['GP'] > 0 else 0,
                    "rebounds_per_game": float(current_season['REB']) / float(current_season['GP']) if current_season['GP'] > 0 else 0,
                    "field_goal_pct": float(current_season['FG_PCT']),
                }
            else:
                return {
                    "success": False,
                    "error": "No season data available"
                }
        
        except Exception as e:
            print(f"Error fetching NBA stats: {e}")
            return self._get_simulated_stats(player_name)
    
    def _get_simulated_stats(self, player_name: str) -> Dict[str, Any]:
        """Simulated stats when API is not available"""
        return {
            "success": True,
            "player_name": player_name,
            "simulated": True,
            "team": "Unknown",
            "position": "Unknown",
            "season": "2024-25",
            "games_played": 45,
            "points_per_game": 22.5,
            "assists_per_game": 5.2,
            "rebounds_per_game": 6.8,
            "field_goal_pct": 0.475,
            "note": "Simulated data - install nba-api for real stats"
        }