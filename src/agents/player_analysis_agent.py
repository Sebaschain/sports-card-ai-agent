from typing import Dict, Any, Optional
from datetime import datetime

from src.tools.nba_stats_tool import NBAStatsTool
from src.tools.nhl_stats_tool import NHLStatsTool
from src.tools.mlb_stats_tool import MLBStatsTool
from src.tools.nfl_stats_tool import NFLStatsTool
from src.tools.soccer_stats_tool import SoccerStatsTool
from src.tools.ball_dont_lie_tool import BallDontLieTool

from src.tools.sports_news_tool import SportsNewsTool
from src.tools.sentiment_tool import SentimentAnalysisTool


class PlayerAnalysisAgent:
    """Agente de análisis de jugadores con datos reales"""

    def __init__(self):
        self.name = "Player Analysis Agent"
        self.nba_tool = NBAStatsTool()
        self.ball_dont_lie = BallDontLieTool()
        self.nhl_tool = NHLStatsTool()
        self.mlb_tool = MLBStatsTool()
        self.nfl_tool = NFLStatsTool()
        self.soccer_tool = SoccerStatsTool()
        self.news_tool = SportsNewsTool()
        self.sentiment_tool = SentimentAnalysisTool()

    async def analyze_player(
        self, player_name: str, sport: str, current_performance: str = None
    ) -> Dict[str, Any]:
        """Analiza el rendimiento de un jugador con datos reales"""

        # Get real stats based on sport
        stats_data = await self._get_real_stats(player_name, sport)

        # Calculate score from real data
        score, trend, rating = self._analyze_stats(
            stats_data, sport, current_performance
        )

        # Generate outlook
        outlook = self._generate_outlook(score, trend, stats_data)

        # Get news and sentiment
        try:
            news_data = await self.news_tool.get_player_news(player_name, sport)
        except Exception as e:
            news_data = {"success": False, "error": str(e)}

        sentiment_data = None
        if news_data.get("success") and news_data.get("news"):
            try:
                sentiment_data = await self.sentiment_tool.analyze_news_sentiment(
                    news_data["news"]
                )
            except Exception as e:
                sentiment_data = {"success": False, "error": str(e)}

        return {
            "agent": self.name,
            "player": player_name,
            "sport": sport,
            "timestamp": datetime.now().isoformat(),
            "real_stats": stats_data,
            "news": news_data,
            "sentiment": sentiment_data,
            "analysis": {
                "performance_score": {
                    "overall_score": score,
                    "trend": trend,
                    "rating": rating,
                },
                "risk_assessment": {
                    "risk_level": "Low"
                    if score >= 75
                    else "Medium"
                    if score >= 60
                    else "High",
                    "risk_score": 100 - score,
                },
                "future_outlook": outlook,
            },
        }

    async def _get_real_stats(self, player_name: str, sport: str) -> Dict[str, Any]:
        """Obtiene estadísticas reales según el deporte (con multi-proveedor)"""
        if sport == "NBA":
            # Intentar primero con NBA API, si falla o es simulado, intentar BallDon'tLie
            stats = await self.nba_tool.get_player_stats(player_name)

            if not stats.get("success") or stats.get("simulated"):
                print(
                    "🔄 NBA Stats falló o es simulado, intentando con Ball Don't Lie..."
                )
                bdl_stats = await self.ball_dont_lie.get_player_stats(player_name)
                if bdl_stats.get("success"):
                    return bdl_stats
            return stats

        elif sport == "NHL":
            return await self.nhl_tool.get_player_stats(player_name)
        elif sport == "MLB":
            return await self.mlb_tool.get_player_stats(player_name)
        elif sport == "NFL":
            return await self.nfl_tool.get_player_stats(player_name)
        elif sport == "Soccer":
            return await self.soccer_tool.get_player_stats(player_name)
        else:
            return {"success": False, "error": "Sport not supported"}

    def _analyze_stats(
        self, stats: Dict[str, Any], sport: str, performance_text: Optional[str]
    ) -> tuple:
        """Analiza las estadísticas y genera score"""

        if not stats.get("success"):
            # Fallback to simple analysis
            score = 75
            trend = "Stable"
            rating = "Good"
            return score, trend, rating

        score = 50  # Base score

        # NBA Analysis
        if sport == "NBA":
            ppg = stats.get("points_per_game", 0)
            apg = stats.get("assists_per_game", 0)
            rpg = stats.get("rebounds_per_game", 0)

            # Score based on performance
            if ppg >= 25:
                score += 25
            elif ppg >= 20:
                score += 20
            elif ppg >= 15:
                score += 15

            if apg >= 7:
                score += 10
            elif apg >= 5:
                score += 5

            if rpg >= 8:
                score += 10
            elif rpg >= 5:
                score += 5

        # NHL Analysis
        elif sport == "NHL":
            ppg = stats.get("points_per_game", 0)
            goals = stats.get("goals", 0)

            if ppg >= 1.3:
                score += 30
            elif ppg >= 1.0:
                score += 25
            elif ppg >= 0.8:
                score += 20

            if goals >= 40:
                score += 15
            elif goals >= 30:
                score += 10

        # MLB Analysis
        elif sport == "MLB":
            avg = stats.get("batting_avg", 0)
            hrs = stats.get("home_runs", 0)

            if avg >= 0.300:
                score += 25
            elif avg >= 0.280:
                score += 20
            elif avg >= 0.260:
                score += 15

            if hrs >= 30:
                score += 15
            elif hrs >= 20:
                score += 10

        # NFL Analysis
        elif sport == "NFL":
            passing_yards = stats.get("passing_yards", 0)
            passing_tds = stats.get("passing_touchdowns", 0)
            rushing_yards = stats.get("rushing_yards", 0)
            rushing_tds = stats.get("rushing_touchdowns", 0)
            receiving_yards = stats.get("receiving_yards", 0)
            receiving_tds = stats.get("receiving_touchdowns", 0)
            receptions = stats.get("receptions", 0)
            interceptions = stats.get("interceptions", 0)

            # Determine key stats based on role magnitude
            is_qb = passing_yards > 500
            is_rb = rushing_yards > 400
            is_wr_te = receiving_yards > 400

            if is_qb:
                if passing_yards >= 4500:
                    score += 25
                elif passing_yards >= 4000:
                    score += 20
                elif passing_yards >= 3500:
                    score += 15

                if passing_tds >= 35:
                    score += 15
                elif passing_tds >= 25:
                    score += 10

                if interceptions <= 10:
                    score += 5
                elif interceptions >= 15:
                    score -= 5

            elif is_rb:
                if rushing_yards >= 1400:
                    score += 25
                elif rushing_yards >= 1100:
                    score += 20
                elif rushing_yards >= 900:
                    score += 15

                total_tds = rushing_tds + receiving_tds
                if total_tds >= 12:
                    score += 15
                elif total_tds >= 8:
                    score += 10

                if receptions >= 50:
                    score += 5

            elif is_wr_te:
                if receiving_yards >= 1400:
                    score += 25
                elif receiving_yards >= 1100:
                    score += 20
                elif receiving_yards >= 900:
                    score += 15

                if receptions >= 100:
                    score += 10
                elif receptions >= 80:
                    score += 5

                if receiving_tds >= 10:
                    score += 10
                elif receiving_tds >= 7:
                    score += 5

            else:
                # Fallback for lower volume players
                if passing_yards > 2000 or rushing_yards > 600 or receiving_yards > 600:
                    score += 10

        # Soccer Analysis
        elif sport == "Soccer":
            goals = stats.get("goals", 0)
            assists = stats.get("assists", 0)
            matches = stats.get("matches_played", 0)
            goals_per_game = stats.get("goals_per_game", 0)
            shots_on_target = stats.get("shots_on_target", 0)

            # Base performance
            if goals >= 20:
                score += 25
            elif goals >= 15:
                score += 20
            elif goals >= 10:
                score += 15

            if assists >= 15:
                score += 15
            elif assists >= 10:
                score += 10
            elif assists >= 5:
                score += 5

            # Efficiency
            if goals_per_game >= 0.7:
                score += 15
            elif goals_per_game >= 0.5:
                score += 10

            # Activity
            if shots_on_target >= 30:
                score += 5

            # Consistency bonus (if matches played is high)
            if matches >= 30:
                score += 5

        # Add bonus from performance text
        if performance_text:
            perf_lower = performance_text.lower()
            if any(
                word in perf_lower
                for word in ["excelente", "excellent", "hot", "racha"]
            ):
                score += 10
                trend = "Improving"
            elif any(word in perf_lower for word in ["lesionado", "injured"]):
                score -= 15
                trend = "Declining"
            else:
                trend = "Stable"
        else:
            trend = "Stable"

        # Limit score
        score = max(0, min(100, score))

        # Determine rating
        if score >= 85:
            rating = "Elite"
        elif score >= 75:
            rating = "Excellent"
        elif score >= 65:
            rating = "Good"
        elif score >= 50:
            rating = "Average"
        else:
            rating = "Below Average"

        return score, trend, rating

    def _generate_outlook(self, score: int, trend: str, stats: Dict[str, Any]) -> str:
        """Genera outlook futuro"""

        if stats.get("simulated"):
            note = " (basado en datos simulados)"
        else:
            note = ""

        if score >= 85 and trend == "Improving":
            return f"Muy positivo - Jugador elite en excelente momento{note}"
        elif score >= 75:
            return f"Positivo - Jugador de alto nivel con buen rendimiento{note}"
        elif score >= 60:
            return f"Neutral - Rendimiento promedio, monitorear{note}"
        elif trend == "Declining":
            return f"Precaución - Tendencia a la baja{note}"
        else:
            return f"Negativo - Bajo rendimiento actual{note}"
