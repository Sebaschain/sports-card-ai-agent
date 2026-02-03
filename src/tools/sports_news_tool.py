from typing import Dict, Any, List
import asyncio
from src.tools.base_tool import BaseTool

try:
    import requests
    from bs4 import BeautifulSoup

    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False
    # No imprimir aquí para evitar problemas de encoding en Windows


class SportsNewsTool(BaseTool):
    """Herramienta para obtener noticias deportivas"""

    def __init__(self):
        self._name = "Sports News Tool"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    @property
    def tool_name(self) -> str:
        return self._name

    async def get_player_news(
        self, player_name: str, sport: str, days: int = 7
    ) -> Dict[str, Any]:
        """
        Obtiene noticias recientes de un jugador usando Google News RSS

        Args:
            player_name: Nombre del jugador
            sport: Deporte (NBA, NHL, MLB)
            days: Días hacia atrás para buscar

        Returns:
            Noticias del jugador
        """
        if not HAS_DEPENDENCIES:
            return self._get_simulated_news(player_name, sport)

        try:
            # Usar Google News RSS feed (no requiere API)
            query = f"{player_name} {sport}".replace(" ", "+")
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

            response = await asyncio.to_thread(
                requests.get, rss_url, headers=self.headers, timeout=10
            )

            if response.status_code == 200:
                # Parse RSS
                soup = BeautifulSoup(response.content, "xml")
                items = soup.find_all("item")[:5]  # Top 5 noticias

                news_list = []
                for item in items:
                    title = item.find("title")
                    link = item.find("link")
                    pub_date = item.find("pubDate")

                    if title and link:
                        news_list.append(
                            {
                                "title": title.text,
                                "url": link.text,
                                "published": pub_date.text if pub_date else "Unknown",
                                "source": "Google News",
                            }
                        )

                return {
                    "success": True,
                    "player": player_name,
                    "sport": sport,
                    "news_count": len(news_list),
                    "news": news_list,
                    "summary": self._generate_news_summary(news_list),
                }
            else:
                return self._get_simulated_news(player_name, sport)

        except Exception as e:
            print(f"Error fetching news: {e}")
            return self._get_simulated_news(player_name, sport)

    def _generate_news_summary(self, news_list: List[Dict]) -> str:
        """Genera un resumen de las noticias"""
        if not news_list:
            return "No hay noticias recientes"

        # Análisis simple de tendencia basado en títulos
        titles = " ".join([n["title"].lower() for n in news_list])

        positive_words = [
            "wins",
            "victory",
            "scores",
            "leads",
            "best",
            "record",
            "amazing",
        ]
        negative_words = ["injury", "loses", "defeat", "worst", "struggles", "benched"]

        positive_count = sum(word in titles for word in positive_words)
        negative_count = sum(word in titles for word in negative_words)

        if negative_count > positive_count:
            sentiment = "⚠️ Noticias recientes sugieren preocupaciones (lesiones o bajo rendimiento)"
        elif positive_count > negative_count:
            sentiment = "✅ Noticias recientes son positivas (buen rendimiento)"
        else:
            sentiment = "➡️ Noticias neutrales, sin tendencia clara"

        return sentiment

    def _get_simulated_news(self, player_name: str, sport: str) -> Dict[str, Any]:
        """Noticias simuladas cuando falla el scraping"""
        return {
            "success": True,
            "player": player_name,
            "sport": sport,
            "simulated": True,
            "news_count": 3,
            "news": [
                {
                    "title": f"{player_name} shows strong performance in recent game",
                    "url": "#",
                    "published": "2 days ago",
                    "source": "Simulated",
                },
                {
                    "title": f"Team scouts watching {player_name} closely",
                    "url": "#",
                    "published": "3 days ago",
                    "source": "Simulated",
                },
                {
                    "title": f"{player_name} contract extension discussed",
                    "url": "#",
                    "published": "5 days ago",
                    "source": "Simulated",
                },
            ],
            "summary": "✅ Noticias recientes son positivas (simuladas)",
            "note": "Simulated news - real news scraping may be blocked",
        }
