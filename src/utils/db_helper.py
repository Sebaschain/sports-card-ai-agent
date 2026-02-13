"""Database helper functions"""

from typing import Dict, Any
from src.utils.database import get_db
from src.utils.repository import CardRepository
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def save_analysis_to_db(
    player_name: str,
    sport: str,
    card_info: Dict[str, Any],
    market: Dict[str, Any],
    performance: Dict[str, Any],
    strategy: Dict[str, Any],
) -> bool:
    """Salva el análisis completo en la base de datos"""
    try:
        # Extraer datos de los diccionarios de los agentes
        market_data = market.get("market_analysis", {})

        year = card_info.get("year", 2024)
        manufacturer = card_info.get("manufacturer", "Unknown")

        with get_db() as db:
            # Get or create player and card first
            player_db = CardRepository.get_or_create_player(
                db=db,
                player_id=f"{sport.lower()}_{player_name.lower().replace(' ', '_')}",
                name=player_name,
                sport=sport,
            )

            card_db = CardRepository.get_or_create_card(
                db=db,
                card_id=f"card_{player_db.id}_{year}_{manufacturer.lower()}",
                player_db=player_db,
                year=year,
                manufacturer=manufacturer,
            )

            # Crear o actualizar registro usando métodos estáticos
            CardRepository.save_analysis(
                db=db,
                card=card_db,
                analysis_type="Advanced Multi-Agent",
                signal=strategy.get("strategy", {}).get("signal", "HOLD"),
                confidence=strategy.get("strategy", {}).get("confidence", 0.5),
                reasoning=strategy.get("strategy", {}).get("reasoning", ""),
                factors=strategy.get("strategy", {}).get("factors", []),
                action_items=strategy.get("strategy", {}).get("action_items", []),
                player_score=performance.get("score", 70),
                player_trend=performance.get("trend"),
                min_price=market_data.get("sold_items", {}).get("min_price", 0),
                max_price=market_data.get("sold_items", {}).get("max_price", 0),
                avg_price=market_data.get("sold_items", {}).get("average_price", 0),
            )

            # También guardar punto de precio si hubo venta
            if market_data.get("sold_items", {}).get("average_price", 0) > 0:
                CardRepository.save_price_point(
                    db=db,
                    card=card_db,
                    price=market_data.get("sold_items", {}).get("average_price", 0),
                    marketplace="eBay",
                    sold=True,
                )

            logger.info(f"Analysis saved to database for {player_name} ({year})")
            return True

    except Exception as e:
        logger.error(f"Error saving analysis to database: {e}", exc_info=True)
        return False
