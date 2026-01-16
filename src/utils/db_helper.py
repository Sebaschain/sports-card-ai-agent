"""Helper functions to save analyses to database"""
import json
from typing import Dict, Any
from src.utils.database import get_db
from src.utils.repository import CardRepository


def save_analysis_to_db(
    player_name: str,
    year: int,
    manufacturer: str,
    sport: str,
    analysis_result: Dict[str, Any],
    analysis_type: str = "simple"
) -> bool:
    """Save an analysis result to database"""
    try:
        with get_db() as db:
            player_id = f"{player_name.lower().replace(' ', '-')}-{sport.lower()}"
            player = CardRepository.get_or_create_player(
                db=db,
                player_id=player_id,
                name=player_name,
                sport=sport
            )
            
            card_id = f"{player_id}-{year}-{manufacturer.lower()}"
            card = CardRepository.get_or_create_card(
                db=db,
                card_id=card_id,
                player_db=player,
                year=year,
                manufacturer=manufacturer
            )
            
            recommendation = analysis_result.get("recommendation", {})
            signal = recommendation.get("signal", "HOLD")
            confidence = recommendation.get("confidence", 0.5)
            
            market = analysis_result.get("detailed_analysis", {}).get("market", {}).get("market_analysis", {})
            player_data = analysis_result.get("detailed_analysis", {}).get("player", {}).get("analysis", {})
            performance = player_data.get("performance_score", {})
            
            if isinstance(confidence, str) and '%' in confidence:
                confidence = float(confidence.rstrip('%')) / 100
            elif not isinstance(confidence, float):
                confidence = float(confidence)
            
            CardRepository.save_analysis(
                db=db,
                card=card,
                analysis_type=analysis_type,
                signal=signal,
                confidence=confidence,
                reasoning=analysis_result.get("reasoning", ""),
                factors=analysis_result.get("action_items", []),
                action_items=analysis_result.get("action_items", []),
                current_price=recommendation.get("price_targets", {}).get("entry_price"),
                target_buy_price=recommendation.get("price_targets", {}).get("entry_price"),
                target_sell_price=recommendation.get("price_targets", {}).get("target_sell_price"),
                stop_loss=recommendation.get("price_targets", {}).get("stop_loss"),
                market_avg_price=market.get("sold_items", {}).get("average_price"),
                market_liquidity=market.get("liquidity"),
                market_sold_count=market.get("sold_items", {}).get("count"),
                player_score=performance.get("overall_score"),
                player_rating=performance.get("rating"),
                player_trend=performance.get("trend")
            )
            
            print(f"✅ Analysis saved to database: {player_name} {year}")
            return True
            
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        import traceback
        traceback.print_exc()
        return False
