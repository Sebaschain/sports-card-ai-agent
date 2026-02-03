"""
Stats cache system to minimize API calls and improve performance
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json


class StatsCache:
    """In-memory cache for sports statistics"""

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_minutes = {
            "player_stats": 60,  # 1 hour
            "team_stats": 120,  # 2 hours
            "game_data": 5,  # 5 minutes for live games
            "season_stats": 1440,  # 24 hours
        }

    def _make_key(self, category: str, identifier: str) -> str:
        """Create cache key"""
        return f"{category}:{identifier}"

    def get(self, category: str, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data if not expired

        Args:
            category: Type of data (player_stats, team_stats, etc.)
            identifier: Unique identifier (player name, team id, etc.)

        Returns:
            Cached data or None if expired/not found
        """
        key = self._make_key(category, identifier)

        if key not in self.cache:
            return None

        entry = self.cache[key]
        ttl = self.ttl_minutes.get(category, 60)

        # Check if expired
        if datetime.now() > entry["expires_at"]:
            del self.cache[key]
            return None

        return entry["data"]

    def set(self, category: str, identifier: str, data: Dict[str, Any]):
        """
        Store data in cache

        Args:
            category: Type of data
            identifier: Unique identifier
            data: Data to cache
        """
        key = self._make_key(category, identifier)
        ttl = self.ttl_minutes.get(category, 60)

        self.cache[key] = {
            "data": data,
            "cached_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=ttl),
        }

    def clear(self, category: Optional[str] = None):
        """Clear cache for a category or all cache"""
        if category is None:
            self.cache.clear()
        else:
            keys_to_delete = [
                k for k in self.cache.keys() if k.startswith(f"{category}:")
            ]
            for key in keys_to_delete:
                del self.cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        by_category = {}

        for key in self.cache.keys():
            category = key.split(":")[0]
            by_category[category] = by_category.get(category, 0) + 1

        return {
            "total_entries": total_entries,
            "by_category": by_category,
            "cache_keys": list(self.cache.keys()),
        }


# Global cache instance
stats_cache = StatsCache()
