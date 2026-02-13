"""Trading Strategy Agent with improved error handling and configurable thresholds."""

import logging
from datetime import datetime
from typing import Any

from src.utils.exceptions import MarketDataError
from src.utils.logging_config import LoggerMixin, get_logger

logger = get_logger(__name__)


class TradingStrategyAgent(LoggerMixin):
    """Agente de estrategia de trading con manejo robusto de errores."""

    # Thresholds for signal generation (configurable)
    BUY_THRESHOLD = 85
    HOLD_THRESHOLD = 70

    # Price multipliers (configurable)
    ENTRY_DISCOUNT = 0.95  # 5% below average
    TARGET_MULTIPLIER = 1.25  # 25% above average
    STOP_LOSS_DISCOUNT = 0.85  # 15% below average

    def __init__(
        self,
        buy_threshold: int = 85,
        hold_threshold: int = 70,
        entry_discount: float = 0.95,
        target_multiplier: float = 1.25,
        stop_loss_discount: float = 0.85,
    ):
        """
        Initialize trading strategy agent.

        Args:
            buy_threshold: Score threshold for BUY signal (default: 85)
            hold_threshold: Score threshold for HOLD signal (default: 70)
            entry_discount: Discount from average price for entry (default: 0.95)
            target_multiplier: Multiplier for target sell price (default: 1.25)
            stop_loss_discount: Discount for stop loss (default: 0.85)
        """
        self.name = "Trading Strategy Agent"
        self.buy_threshold = buy_threshold
        self.hold_threshold = hold_threshold
        self.entry_discount = entry_discount
        self.target_multiplier = target_multiplier
        self.stop_loss_discount = stop_loss_discount

    def _get_player_score(self, player_analysis: dict[str, Any]) -> tuple[int, bool]:
        """
        Extract player score from analysis.

        Returns:
            Tuple of (score, is_estimated)
        """
        player_data = player_analysis.get("analysis", {})

        if not player_data:
            logger.warning("Player analysis is empty, using default score")
            return 50, True

        score_data = player_data.get("performance_score", {})

        if not score_data:
            logger.warning("Performance score not found in player analysis")
            return 50, True

        score = score_data.get("overall_score")

        if score is None:
            logger.warning("Overall score not found in performance data")
            return 50, True

        return int(score), False

    def _get_average_price(self, market_analysis: dict[str, Any]) -> tuple[float, bool]:
        """
        Extract average price from market analysis.

        Returns:
            Tuple of (price, is_estimated)
        """
        market_data = market_analysis.get("market_analysis", {})

        if not market_data:
            logger.warning("Market analysis is empty, price unknown")
            return 0.0, True

        sold_items = market_data.get("sold_items", {})

        if not sold_items:
            logger.warning("Sold items data not found")
            return 0.0, True

        avg_price = sold_items.get("average_price")

        if avg_price is None or avg_price <= 0:
            logger.warning("Invalid average price")
            return 0.0, True

        return float(avg_price), False

    def _determine_signal(self, player_score: int) -> tuple[str, float]:
        """Determine trading signal based on player score."""
        if player_score >= self.buy_threshold:
            return "BUY", 0.80
        elif player_score >= self.hold_threshold:
            return "HOLD", 0.65
        else:
            return "SELL", 0.70

    def _calculate_risk_reward(self, avg_price: float, player_score: int) -> dict[str, Any]:
        """Calculate risk/reward ratio based on market conditions."""
        # Base risk/reward ratio
        ratio = 2.5

        # Adjust based on player score
        if player_score >= 90:
            assessment = "Favorable - Alto potencial de apreciación"
            ratio = 3.0
        elif player_score >= 80:
            assessment = "Favorable - Buena relación riesgo/recompensa"
            ratio = 2.5
        elif player_score >= 70:
            assessment = "Moderada - Considere otros factores"
            ratio = 2.0
        else:
            assessment = "Desfavorable - Alto riesgo"
            ratio = 1.5

        return {"ratio": f"{ratio}:1", "assessment": assessment}

    def _generate_reasoning(
        self,
        signal: str,
        player_score: int,
        avg_price: float,
        player_name: str,
        is_price_estimated: bool,
    ) -> str:
        """Generate human-readable reasoning for the strategy."""
        opportunity = {
            "BUY": "una buena",
            "HOLD": "una moderada",
            "SELL": "poca",
        }.get(signal, "desconocida")

        price_note = ""
        if is_price_estimated:
            price_note = " (precio estimado basado en datos limitados)"

        opportunity_text = {
            "BUY": "una buena",
            "HOLD": "una moderada",
            "SELL": "poca",
        }.get(signal, "desconocida")

        reasoning = (
            f"Recomendación de {signal}. "
            f"El jugador {player_name} tiene un score de {player_score}/100. "
            f"Precio promedio de mercado: ${avg_price:.2f}{price_note}. "
            f"La tarjeta presenta {opportunity_text} oportunidad de inversión."
        )

        return reasoning

    def _generate_action_items(self, signal: str) -> list[str]:
        """Generate action items based on signal."""
        actions = {
            "BUY": [
                "Buscar oportunidades de compra a precios favorables",
                "Verificar autenticidad antes de comprar",
                "Considerar estado de la tarjeta (grado PSA/BGS)",
            ],
            "HOLD": [
                "Mantener posición actual",
                "Monitorear rendimiento del jugador",
                "Establecer alertas de precio para movimiento",
            ],
            "SELL": [
                "Considerar venta si el precio es aceptable",
                "Evaluar momento óptimo para vender",
                "Diversificar hacia jugadores con mejor outlook",
            ],
        }

        base_actions = [
            "Revisar análisis de mercado actualizado",
            "Consultar noticias recientes del jugador",
        ]

        return actions.get(signal, actions["HOLD"]) + base_actions

    async def generate_trading_strategy(
        self,
        market_analysis: dict[str, Any],
        player_analysis: dict[str, Any],
        card_info: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Genera estrategia de trading con manejo robusto de errores.

        Args:
            market_analysis: Analysis from market research agent
            player_analysis: Analysis from player analysis agent
            card_info: Information about the card

        Returns:
            Dict with trading strategy
        """
        context_id = f"{datetime.now().isoformat()}_{id(self)}"
        player_name = card_info.get("player", "Unknown")

        self._log_with_context(
            logging.INFO,
            f"Generating strategy for {player_name}",
            {"context_id": context_id, "player": player_name},
        )

        try:
            # Extract player score
            player_score, is_score_estimated = self._get_player_score(player_analysis)

            # Extract average price
            avg_price, is_price_estimated = self._get_average_price(market_analysis)

            # Validate we have enough data
            if avg_price <= 0:
                raise MarketDataError(
                    f"Unable to determine average price for {player_name}",
                    data_source="market_analysis",
                )

            # Determine signal
            signal, confidence = self._determine_signal(player_score)

            # Calculate price targets
            entry_price = avg_price * self.entry_discount
            target_sell = avg_price * self.target_multiplier
            stop_loss = avg_price * self.stop_loss_discount

            # Calculate risk/reward
            risk_reward = self._calculate_risk_reward(avg_price, player_score)

            # Generate reasoning
            reasoning = self._generate_reasoning(
                signal, player_score, avg_price, player_name, is_price_estimated
            )

            # Generate action items
            action_items = self._generate_action_items(signal)

            result = {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "context_id": context_id,
                "card": card_info,
                "data_quality": {
                    "player_score_estimated": is_score_estimated,
                    "price_estimated": is_price_estimated,
                },
                "strategy": {
                    "signal": signal,
                    "confidence": confidence,
                    "price_targets": {
                        "entry_price": round(entry_price, 2),
                        "target_sell_price": round(target_sell, 2),
                        "stop_loss": round(stop_loss, 2),
                        "average_price": round(avg_price, 2),
                    },
                    "risk_reward": risk_reward,
                    "reasoning": reasoning,
                    "action_items": action_items,
                },
            }

            self._log_with_context(
                logging.INFO,
                f"Generated strategy for {player_name}: {signal} (conf: {confidence})",
                {"context_id": context_id, "signal": signal, "confidence": confidence},
            )

            return result

        except MarketDataError as e:
            self._log_with_context(
                logging.ERROR,
                f"Market data error for {player_name}: {e.message}",
                {"context_id": context_id, "error": e.message},
            )
            return self._create_error_response(card_info, context_id, str(e))

        except Exception as e:
            self._log_with_context(
                logging.ERROR,
                f"Unexpected error generating strategy for {player_name}",
                {"context_id": context_id, "error": str(e)},
                exc_info=True,
            )
            return self._create_error_response(
                card_info, context_id, "Error interno al generar estrategia"
            )

    def _create_error_response(
        self, card_info: dict[str, Any], context_id: str, error: str
    ) -> dict[str, Any]:
        """Create error response when strategy generation fails."""
        return {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "context_id": context_id,
            "card": card_info,
            "error": error,
            "strategy": None,
        }

    def get_thresholds(self) -> dict[str, Any]:
        """Get current threshold configuration."""
        return {
            "buy_threshold": self.buy_threshold,
            "hold_threshold": self.hold_threshold,
            "entry_discount": self.entry_discount,
            "target_multiplier": self.target_multiplier,
            "stop_loss_discount": self.stop_loss_discount,
        }

    def set_thresholds(
        self,
        buy_threshold: int | None = None,
        hold_threshold: int | None = None,
        entry_discount: float | None = None,
        target_multiplier: float | None = None,
        stop_loss_discount: float | None = None,
    ) -> None:
        """Update threshold configuration."""
        if buy_threshold is not None:
            self.buy_threshold = buy_threshold
        if hold_threshold is not None:
            self.hold_threshold = hold_threshold
        if entry_discount is not None:
            self.entry_discount = entry_discount
        if target_multiplier is not None:
            self.target_multiplier = target_multiplier
        if stop_loss_discount is not None:
            self.stop_loss_discount = stop_loss_discount

        logger.info(
            f"Updated thresholds: buy={self.buy_threshold}, "
            f"hold={self.hold_threshold}, entry={self.entry_discount}, "
            f"target={self.target_multiplier}, stop={self.stop_loss_discount}"
        )
