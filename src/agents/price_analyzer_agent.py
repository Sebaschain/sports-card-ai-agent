"""
Agente de Análisis de Precios
Analiza precios de tarjetas deportivas y genera recomendaciones
"""

from typing import List, Optional
from datetime import datetime
import statistics

from langchain_openai import ChatOpenAI

from src.models.card import (
    Card,
    Player,
    Sport,
    CardCondition,
    PricePoint,
    TradingSignal,
    TradingRecommendation,
)
from src.utils.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class PriceAnalyzerAgent:
    """
    Agente que analiza precios de tarjetas y genera recomendaciones

    Este agente puede:
    1. Analizar tendencias de precios
    2. Comparar precios entre diferentes marketplaces
    3. Generar señales de compra/venta
    4. Considerar el rendimiento del jugador
    """

    def __init__(
        self, model: str = "gpt-4o-mini", temperature: float = 0.1, verbose: bool = True
    ):
        """
        Inicializa el agente de análisis de precios

        Args:
            model: Modelo de OpenAI a usar
            temperature: Temperatura para generación (0 = más determinístico)
            verbose: Si mostrar logs detallados
        """
        self.verbose = verbose

        # Inicializar LLM
        if settings.OPENAI_API_KEY:
            try:
                self.llm = ChatOpenAI(
                    model=model,
                    temperature=temperature,
                    api_key=settings.OPENAI_API_KEY,
                )
                self.has_llm = True
                if verbose:
                    logger.info(
                        "OpenAI API configurada correctamente para PriceAnalyzer"
                    )
            except Exception as e:
                self.llm = None
                self.has_llm = False
                if verbose:
                    logger.error(f"Error al configurar OpenAI en PriceAnalyzer: {e}")
                    logger.info("Usando análisis basado en reglas para PriceAnalyzer")
        else:
            self.llm = None
            self.has_llm = False
            if verbose:
                logger.info(
                    "OpenAI API no configurada. Usando análisis basado en reglas para PriceAnalyzer."
                )

    def analyze_card(
        self,
        card: Card,
        price_history: List[PricePoint],
        player_performance: Optional[str] = None,
    ) -> TradingRecommendation:
        """
        Analiza una tarjeta y genera recomendación

        Args:
            card: Información de la tarjeta
            price_history: Historial de precios
            player_performance: Descripción del rendimiento del jugador

        Returns:
            TradingRecommendation con señal y razonamiento
        """
        if not price_history:
            return self._create_no_data_recommendation(card)

        # Extraer precios
        prices = [p.price for p in price_history]
        current_price = prices[-1] if prices else 0
        avg_price = statistics.mean(prices) if prices else 0

        # Usar análisis basado en reglas
        return self._analyze_with_rules(
            card, prices, current_price, avg_price, player_performance
        )

    def _analyze_with_rules(
        self,
        card: Card,
        prices: List[float],
        current_price: float,
        avg_price: float,
        player_performance: Optional[str],
    ) -> TradingRecommendation:
        """Análisis basado en reglas (sin LLM)"""

        # Calcular tendencia
        if len(prices) >= 5:
            recent_avg = statistics.mean(prices[-5:])
            older_avg = statistics.mean(prices[:5])
            trend = ((recent_avg - older_avg) / older_avg) * 100
        else:
            trend = 0

        # Comparar con promedio
        if avg_price > 0:
            price_vs_avg = ((current_price - avg_price) / avg_price) * 100
        else:
            price_vs_avg = 0

        # Factores para considerar
        factors = []
        signal = TradingSignal.HOLD
        confidence = 0.5

        # Factor 1: Tendencia de precio
        if trend > 15:
            factors.append(f"Precio subiendo fuertemente (+{trend:.1f}%)")
            signal = TradingSignal.SELL
            confidence += 0.15
        elif trend > 5:
            factors.append(f"Precio en tendencia alcista (+{trend:.1f}%)")
            signal = TradingSignal.HOLD
            confidence += 0.05
        elif trend < -15:
            factors.append(f"Precio bajando fuertemente ({trend:.1f}%)")
            signal = TradingSignal.BUY
            confidence += 0.15
        elif trend < -5:
            factors.append(f"Precio en tendencia bajista ({trend:.1f}%)")
            signal = TradingSignal.BUY
            confidence += 0.1
        else:
            factors.append("Precio estable")

        # Factor 2: Comparación con promedio
        if price_vs_avg < -15:
            factors.append(f"Precio {abs(price_vs_avg):.1f}% bajo el promedio")
            if signal != TradingSignal.SELL:
                signal = TradingSignal.BUY
            confidence += 0.15
        elif price_vs_avg > 15:
            factors.append(f"Precio {price_vs_avg:.1f}% sobre el promedio")
            if signal != TradingSignal.BUY:
                signal = TradingSignal.SELL
            confidence += 0.1

        # Factor 3: Características de la tarjeta
        if card.variant and "rookie" in card.variant.lower():
            factors.append("Rookie card - alta demanda")
            confidence += 0.1

        if card.graded and card.grade and card.grade >= 9:
            factors.append(f"Tarjeta graduada {card.grade} - premium")
            confidence += 0.1

        # Factor 4: Performance del jugador
        if player_performance:
            perf_lower = player_performance.lower()
            if any(
                word in perf_lower
                for word in ["hot", "excelente", "racha", "streak", "excellent"]
            ):
                factors.append("Jugador en racha caliente")
                if signal == TradingSignal.HOLD:
                    signal = TradingSignal.BUY
                confidence += 0.15
            elif any(
                word in perf_lower
                for word in ["injured", "lesionado", "lesión", "injury"]
            ):
                factors.append("Jugador lesionado - riesgo")
                if signal == TradingSignal.HOLD:
                    signal = TradingSignal.SELL
                confidence += 0.1

        # Limitar confianza entre 0.3 y 0.95
        confidence = max(0.3, min(0.95, confidence))

        # Generar razonamiento
        reasoning = self._generate_reasoning(signal, factors, trend, price_vs_avg)

        # Calcular precios objetivo
        if signal in [TradingSignal.BUY, TradingSignal.STRONG_BUY]:
            target_buy = current_price * 0.90
            target_sell = None
        elif signal in [TradingSignal.SELL, TradingSignal.STRONG_SELL]:
            target_buy = None
            target_sell = current_price * 1.20
        else:
            target_buy = None
            target_sell = None

        return TradingRecommendation(
            card=card,
            signal=signal,
            confidence=confidence,
            current_price=current_price,
            target_buy_price=target_buy,
            target_sell_price=target_sell,
            reasoning=reasoning,
            factors=factors,
            timestamp=datetime.now(),
        )

    def _generate_reasoning(
        self,
        signal: TradingSignal,
        factors: List[str],
        trend: float,
        price_vs_avg: float,
    ) -> str:
        """Genera el razonamiento textual de la recomendación"""

        signal_text = {
            TradingSignal.STRONG_BUY: "Recomendación FUERTE de COMPRA",
            TradingSignal.BUY: "Recomendación de COMPRA",
            TradingSignal.HOLD: "Recomendación de MANTENER",
            TradingSignal.SELL: "Recomendación de VENTA",
            TradingSignal.STRONG_SELL: "Recomendación FUERTE de VENTA",
        }

        reasoning = f"{signal_text[signal]}. "

        if signal in [TradingSignal.BUY, TradingSignal.STRONG_BUY]:
            reasoning += "La tarjeta presenta una oportunidad de compra debido a "
        elif signal in [TradingSignal.SELL, TradingSignal.STRONG_SELL]:
            reasoning += "Se recomienda considerar vender porque "
        else:
            reasoning += "La tarjeta muestra equilibrio en el mercado con "

        reasoning += f"una tendencia de precio del {trend:+.1f}% y un precio "
        reasoning += f"actual {abs(price_vs_avg):.1f}% {'sobre' if price_vs_avg > 0 else 'bajo'} el promedio histórico."

        return reasoning

    def _create_no_data_recommendation(self, card: Card) -> TradingRecommendation:
        """Crea una recomendación cuando no hay datos"""
        return TradingRecommendation(
            card=card,
            signal=TradingSignal.HOLD,
            confidence=0.0,
            current_price=0.0,
            reasoning="No hay suficientes datos de precios para generar una recomendación",
            factors=["Sin historial de precios disponible"],
            timestamp=datetime.now(),
        )
