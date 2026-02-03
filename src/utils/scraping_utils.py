"""
Scraping utilities for sports data
Provides common functionality for web scraping with rate limiting and error handling
"""

import time
import random
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class ScrapingUtils:
    """Utilities for web scraping with best practices"""

    def __init__(self):
        self.ua = UserAgent()
        self.last_request_time = {}
        self.min_delay = 1.0  # Minimum delay between requests in seconds

    def get_headers(self) -> Dict[str, str]:
        """Get randomized headers for requests"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def rate_limit(self, domain: str):
        """Enforce rate limiting per domain"""
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.min_delay:
                sleep_time = self.min_delay - elapsed + random.uniform(0, 0.5)
                time.sleep(sleep_time)

        self.last_request_time[domain] = time.time()

    async def fetch_page(self, url: str, timeout: int = 10) -> Optional[str]:
        """
        Fetch a web page with rate limiting and error handling

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            HTML content or None if failed
        """
        try:
            # Extract domain for rate limiting
            from urllib.parse import urlparse

            domain = urlparse(url).netloc
            self.rate_limit(domain)

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=self.get_headers())
                response.raise_for_status()
                return response.text

        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching {url}: {e.response.status_code}")
            return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_html(self, html: str) -> Optional[BeautifulSoup]:
        """Parse HTML content with BeautifulSoup"""
        try:
            return BeautifulSoup(html, "lxml")
        except Exception as e:
            print(f"Error parsing HTML: {e}")
            return None


# Global instance
scraper = ScrapingUtils()
