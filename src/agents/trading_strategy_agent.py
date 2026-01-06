"""Trading Strategy Agent"""
from typing import Dict, Any
from datetime import datetime


class TradingStrategyAgent:
    """Agente de estrategia de trading"""
    
    def __init__(self):
        self.name = "Trading Strategy Agent"
    
    def generate_trading_strategy(
        self,
        market_analysis: Dict[str, Any],
        player_analysis: Dict[str, Any],
        card_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Genera estrategia de trading"""
        
        market_data = market_analysis.get("market_analysis", {})
        player_data = player_analysis.get("analysis", {})
        
        player_score = player_data.get("performance_score", {}).get("overall_score", 70)
        avg_price = market_data.get("sold_items", {}).get("average_price", 500)
        
        if player_score >= 85:
            signal = "BUY"
            confidence = 0.80
        elif player_score >= 70:
            signal = "HOLD"
            confidence = 0.65
        else:
            signal = "SELL"
            confidence = 0.70
        
        entry_price = avg_price * 0.95
        target_sell = avg_price * 1.25
        stop_loss = avg_price * 0.85
        
        reasoning = (
            f"Recomendación de {signal}. "
            f"El jugador tiene un score de {player_score}/100. "
            f"Precio promedio de mercado: ${avg_price:.2f}. "
            f"La tarjeta presenta {'una buena' if signal == 'BUY' else 'una moderada' if signal == 'HOLD' else 'poca'} "
            f"oportunidad de inversión."
        )
        
        return {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "card": card_info,
            "strategy": {
                "signal": signal,
                "confidence": confidence,
                "price_targets": {
                    "entry_price": round(entry_price, 2),
                    "target_sell_price": round(target_sell, 2),
                    "stop_loss": round(stop_loss, 2)
                },
                "risk_reward": {"ratio": "2.5:1", "assessment": "Favorable"},
                "reasoning": reasoning,
                "action_items": [
                    f"{'Buscar oportunidades de compra' if signal == 'BUY' else 'Mantener posición' if signal == 'HOLD' else 'Considerar venta'}",
                    "Monitorear rendimiento del jugador",
                    "Establecer alertas de precio"
                ]
            }
        }