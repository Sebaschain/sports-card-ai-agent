from typing import Dict, Any, List
import asyncio
from src.tools.base_tool import BaseTool

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    from textblob import TextBlob

    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False


class SentimentAnalysisTool(BaseTool):
    """Herramienta de análisis de sentimientos"""

    def __init__(self):
        self._name = "Sentiment Analysis Tool"
        if HAS_DEPENDENCIES:
            self.vader = SentimentIntensityAnalyzer()
        else:
            self.vader = None

    @property
    def tool_name(self) -> str:
        return self._name

    async def analyze_news_sentiment(
        self, news_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analiza el sentimiento de una lista de noticias

        Args:
            news_items: Lista de noticias con campo 'title'

        Returns:
            Análisis de sentimiento agregado
        """
        if not news_items:
            return {"success": False, "error": "No news items to analyze"}

        if not HAS_DEPENDENCIES or not self.vader:
            # Modo simulado cuando no hay dependencias
            return {
                "success": True,
                "overall_sentiment": "Neutral",
                "sentiment_score": 0.0,
                "confidence": 0.5,
                "distribution": {
                    "positive": 1,
                    "neutral": len(news_items) - 1,
                    "negative": 0,
                },
                "individual_sentiments": [],
                "recommendation": "➡️ Sentimiento neutral - análisis simulado (instalar textblob y vaderSentiment para análisis real)",
            }

        sentiments = []
        for news in news_items:
            title = news.get("title", "")
            if title:
                # Wrap CPU-bound NLP in to_thread
                def _analyze_single(text):
                    vs = self.vader.polarity_scores(text)
                    tb = TextBlob(text)
                    return {
                        "vader_compound": vs["compound"],
                        "textblob_polarity": tb.sentiment.polarity,
                    }

                analysis = await asyncio.to_thread(_analyze_single, title)

                sentiments.append(
                    {
                        "title": title,
                        "vader_compound": analysis["vader_compound"],
                        "textblob_polarity": analysis["textblob_polarity"],
                        "classification": self._classify_sentiment(
                            analysis["vader_compound"]
                        ),
                    }
                )

        # Calcular sentimiento agregado
        avg_vader = sum(s["vader_compound"] for s in sentiments) / len(sentiments)

        # Clasificación general
        overall_sentiment = self._classify_sentiment(avg_vader)

        # Distribución
        positive_count = sum(1 for s in sentiments if s["classification"] == "Positive")
        neutral_count = sum(1 for s in sentiments if s["classification"] == "Neutral")
        negative_count = sum(1 for s in sentiments if s["classification"] == "Negative")

        return {
            "success": True,
            "overall_sentiment": overall_sentiment,
            "sentiment_score": round(avg_vader, 3),
            "confidence": self._calculate_confidence(sentiments),
            "distribution": {
                "positive": positive_count,
                "neutral": neutral_count,
                "negative": negative_count,
            },
            "individual_sentiments": sentiments,
            "recommendation": self._generate_sentiment_recommendation(
                overall_sentiment
            ),
        }

    def _classify_sentiment(self, compound_score: float) -> str:
        """Clasifica el sentimiento basado en el score"""
        if compound_score >= 0.05:
            return "Positive"
        elif compound_score <= -0.05:
            return "Negative"
        else:
            return "Neutral"

    def _calculate_confidence(self, sentiments: List[Dict]) -> float:
        """Calcula confianza basada en consistencia de sentimientos"""
        if not sentiments:
            return 0.0

        # Confianza alta si todos apuntan en la misma dirección
        classifications = [s["classification"] for s in sentiments]
        most_common = max(set(classifications), key=classifications.count)
        consistency = classifications.count(most_common) / len(classifications)

        return round(consistency, 2)

    def _generate_sentiment_recommendation(self, sentiment: str) -> str:
        """Genera recomendación basada en sentimiento"""
        if sentiment == "Positive":
            return "📈 El sentimiento público es positivo - puede aumentar la demanda de tarjetas"
        elif sentiment == "Negative":
            return "📉 El sentimiento público es negativo - posible impacto en precios"
        else:
            return "➡️ Sentimiento neutral - monitorear de cerca"
