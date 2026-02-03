"""
Repository layer for database operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.models.db_models import (
    PlayerDB,
    CardDB,
    PricePointDB,
    AnalysisDB,
    PortfolioItemDB,
    SportEnum,
    SignalEnum,
)


class CardRepository:
    """Repository for card-related operations"""

    @staticmethod
    def get_or_create_player(
        db: Session,
        player_id: str,
        name: str,
        sport: str,
        team: Optional[str] = None,
        position: Optional[str] = None,
    ) -> PlayerDB:
        """Get existing player or create new one"""
        player = db.query(PlayerDB).filter(PlayerDB.player_id == player_id).first()

        if not player:
            player = PlayerDB(
                player_id=player_id,
                name=name,
                sport=SportEnum[sport],
                team=team,
                position=position,
            )
            db.add(player)
            db.flush()

        return player

    @staticmethod
    def get_or_create_card(
        db: Session,
        card_id: str,
        player_db: PlayerDB,
        year: int,
        manufacturer: str,
        **kwargs,
    ) -> CardDB:
        """Get existing card or create new one"""
        card = db.query(CardDB).filter(CardDB.card_id == card_id).first()

        if not card:
            card = CardDB(
                card_id=card_id,
                player_id=player_db.id,
                year=year,
                manufacturer=manufacturer,
                **kwargs,
            )
            db.add(card)
            db.flush()

        return card

    @staticmethod
    def save_analysis(
        db: Session,
        card: CardDB,
        analysis_type: str,
        signal: str,
        confidence: float,
        reasoning: str,
        factors: List[str],
        action_items: List[str],
        **kwargs,
    ) -> AnalysisDB:
        """Save an analysis to database"""
        analysis = AnalysisDB(
            card_id=card.id,
            analysis_type=analysis_type,
            signal=SignalEnum[signal],
            confidence=confidence,
            reasoning=reasoning,
            factors=json.dumps(factors),
            action_items=json.dumps(action_items),
            **kwargs,
        )
        db.add(analysis)
        db.flush()
        return analysis

    @staticmethod
    def get_card_analyses(
        db: Session, card_id: str, limit: int = 10
    ) -> List[AnalysisDB]:
        """Get recent analyses for a card"""
        card = db.query(CardDB).filter(CardDB.card_id == card_id).first()
        if not card:
            return []

        return (
            db.query(AnalysisDB)
            .filter(AnalysisDB.card_id == card.id)
            .order_by(desc(AnalysisDB.timestamp))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_all_analyses(
        db: Session,
        limit: int = 50,
        sport: Optional[str] = None,
        signal: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all analyses with filters"""
        query = (
            db.query(AnalysisDB, CardDB, PlayerDB)
            .join(CardDB, AnalysisDB.card_id == CardDB.id)
            .join(PlayerDB, CardDB.player_id == PlayerDB.id)
        )

        if sport:
            query = query.filter(PlayerDB.sport == SportEnum[sport])

        if signal:
            query = query.filter(AnalysisDB.signal == SignalEnum[signal])

        results = query.order_by(desc(AnalysisDB.timestamp)).limit(limit).all()

        # Format results
        formatted = []
        for analysis, card, player in results:
            formatted.append(
                {
                    "id": analysis.id,
                    "timestamp": analysis.timestamp,
                    "player_name": player.name,
                    "sport": player.sport.value,
                    "year": card.year,
                    "manufacturer": card.manufacturer,
                    "signal": analysis.signal.value,
                    "confidence": analysis.confidence,
                    "current_price": analysis.current_price,
                    "reasoning": analysis.reasoning,
                    "analysis_type": analysis.analysis_type,
                }
            )

        return formatted

    @staticmethod
    def save_price_point(
        db: Session,
        card: CardDB,
        price: float,
        marketplace: str,
        sold: bool = False,
        **kwargs,
    ) -> PricePointDB:
        """Save a price point"""
        price_point = PricePointDB(
            card_id=card.id, price=price, marketplace=marketplace, sold=sold, **kwargs
        )
        db.add(price_point)
        db.flush()
        return price_point

    @staticmethod
    def get_price_history(
        db: Session, card_id: str, days: int = 30
    ) -> List[PricePointDB]:
        """Get price history for a card"""
        card = db.query(CardDB).filter(CardDB.card_id == card_id).first()
        if not card:
            return []

        since_date = datetime.now() - timedelta(days=days)

        return (
            db.query(PricePointDB)
            .filter(
                PricePointDB.card_id == card.id, PricePointDB.timestamp >= since_date
            )
            .order_by(PricePointDB.timestamp)
            .all()
        )

    @staticmethod
    def get_statistics(db: Session, days: int = 14) -> Dict[str, Any]:
        """Get advanced database statistics for dashboard"""

        # Basic counts
        stats = {
            "total_players": db.query(PlayerDB).count(),
            "total_cards": db.query(CardDB).count(),
            "total_analyses": db.query(AnalysisDB).count(),
            "total_prices": db.query(PricePointDB).count(),
        }

        # Recent activity (last 7 days)
        last_week = datetime.now() - timedelta(days=7)
        stats["recent_analyses"] = (
            db.query(AnalysisDB).filter(AnalysisDB.timestamp >= last_week).count()
        )

        # Analysis trend (daily counts for last 14 days)
        trend_data = []
        for i in range(days):
            target_date = datetime.now().date() - timedelta(days=i)
            next_day = target_date + timedelta(days=1)

            count = (
                db.query(AnalysisDB)
                .filter(
                    AnalysisDB.timestamp
                    >= datetime.combine(target_date, datetime.min.time()),
                    AnalysisDB.timestamp
                    < datetime.combine(next_day, datetime.min.time()),
                )
                .count()
            )

            trend_data.append(
                {"date": target_date.strftime("%Y-%m-%d"), "count": count}
            )

        stats["daily_trend"] = list(reversed(trend_data))

        # Signals distribution
        signals = (
            db.query(AnalysisDB.signal, func.count(AnalysisDB.id))
            .group_by(AnalysisDB.signal)
            .all()
        )
        stats["signals_distribution"] = {s[0].value: s[1] for s in signals}

        # Sport distribution
        sports = (
            db.query(PlayerDB.sport, func.count(AnalysisDB.id))
            .join(CardDB, PlayerDB.id == CardDB.player_id)
            .join(AnalysisDB, CardDB.id == AnalysisDB.card_id)
            .group_by(PlayerDB.sport)
            .all()
        )

        stats["sport_distribution"] = {s[0].value: s[1] for s in sports}

        # Top analyzed players
        top_players = (
            db.query(PlayerDB.name, func.count(AnalysisDB.id))
            .join(CardDB, PlayerDB.id == CardDB.player_id)
            .join(AnalysisDB, CardDB.id == AnalysisDB.card_id)
            .group_by(PlayerDB.name)
            .order_by(desc(func.count(AnalysisDB.id)))
            .limit(5)
            .all()
        )

        stats["top_players"] = [{"name": p[0], "count": p[1]} for p in top_players]

        return stats

    @staticmethod
    def add_to_portfolio(
        db: Session,
        card: CardDB,
        purchase_price: float,
        purchase_date: datetime,
        quantity: int = 1,
        notes: str = "",
    ) -> PortfolioItemDB:
        """Add a card to portfolio"""
        portfolio_item = PortfolioItemDB(
            card_id=card.id,
            purchase_price=purchase_price,
            purchase_date=purchase_date,
            quantity=quantity,
            current_value=purchase_price,  # Initial value
            notes=notes,
            is_active=True,
        )
        db.add(portfolio_item)
        db.flush()
        return portfolio_item

    @staticmethod
    def get_portfolio(db: Session, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all portfolio items"""
        query = (
            db.query(PortfolioItemDB, CardDB, PlayerDB)
            .join(CardDB, PortfolioItemDB.card_id == CardDB.id)
            .join(PlayerDB, CardDB.player_id == PlayerDB.id)
        )

        if active_only:
            query = query.filter(PortfolioItemDB.is_active)

        results = query.order_by(desc(PortfolioItemDB.purchase_date)).all()

        formatted = []
        for portfolio_item, card, player in results:
            gain_loss = (
                portfolio_item.current_value or 0
            ) - portfolio_item.purchase_price
            gain_loss_pct = (
                (gain_loss / portfolio_item.purchase_price * 100)
                if portfolio_item.purchase_price > 0
                else 0
            )

            formatted.append(
                {
                    "id": portfolio_item.id,
                    "player_name": player.name,
                    "sport": player.sport.value,
                    "year": card.year,
                    "manufacturer": card.manufacturer,
                    "purchase_price": portfolio_item.purchase_price,
                    "current_value": portfolio_item.current_value
                    or portfolio_item.purchase_price,
                    "quantity": portfolio_item.quantity,
                    "total_value": (
                        portfolio_item.current_value or portfolio_item.purchase_price
                    )
                    * portfolio_item.quantity,
                    "gain_loss": gain_loss * portfolio_item.quantity,
                    "gain_loss_pct": gain_loss_pct,
                    "purchase_date": portfolio_item.purchase_date,
                    "notes": portfolio_item.notes,
                    "is_active": portfolio_item.is_active,
                }
            )

        return formatted

    @staticmethod
    def update_portfolio_value(
        db: Session, portfolio_item_id: int, new_value: float
    ) -> PortfolioItemDB:
        """Update current value of a portfolio item"""
        portfolio_item = (
            db.query(PortfolioItemDB)
            .filter(PortfolioItemDB.id == portfolio_item_id)
            .first()
        )

        if portfolio_item:
            portfolio_item.current_value = new_value
            portfolio_item.last_updated = datetime.now()
            db.flush()

        return portfolio_item

    @staticmethod
    def remove_from_portfolio(
        db: Session,
        portfolio_item_id: int,
        sell_price: Optional[float] = None,
        sell_date: Optional[datetime] = None,
    ) -> PortfolioItemDB:
        """Remove/sell a card from portfolio"""
        portfolio_item = (
            db.query(PortfolioItemDB)
            .filter(PortfolioItemDB.id == portfolio_item_id)
            .first()
        )

        if portfolio_item:
            portfolio_item.is_active = False
            portfolio_item.sell_price = sell_price
            portfolio_item.sell_date = sell_date or datetime.now()
            db.flush()

        return portfolio_item

    @staticmethod
    def get_portfolio_stats(db: Session) -> Dict[str, Any]:
        """Get portfolio statistics"""
        active_items = db.query(PortfolioItemDB).filter(PortfolioItemDB.is_active).all()

        if not active_items:
            return {
                "total_items": 0,
                "total_invested": 0,
                "current_value": 0,
                "total_gain_loss": 0,
                "total_gain_loss_pct": 0,
                "best_performer": None,
                "worst_performer": None,
            }

        total_invested = sum(
            item.purchase_price * item.quantity for item in active_items
        )
        current_value = sum(
            (item.current_value or item.purchase_price) * item.quantity
            for item in active_items
        )
        total_gain_loss = current_value - total_invested
        total_gain_loss_pct = (
            (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
        )

        # Best and worst performers
        items_with_performance = []
        for item in active_items:
            gain_loss_pct = (
                (
                    ((item.current_value or item.purchase_price) - item.purchase_price)
                    / item.purchase_price
                    * 100
                )
                if item.purchase_price > 0
                else 0
            )
            items_with_performance.append((item.id, gain_loss_pct))

        best = (
            max(items_with_performance, key=lambda x: x[1])
            if items_with_performance
            else None
        )
        worst = (
            min(items_with_performance, key=lambda x: x[1])
            if items_with_performance
            else None
        )

        return {
            "total_items": len(active_items),
            "total_invested": round(total_invested, 2),
            "current_value": round(current_value, 2),
            "total_gain_loss": round(total_gain_loss, 2),
            "total_gain_loss_pct": round(total_gain_loss_pct, 2),
            "best_performer_id": best[0] if best else None,
            "best_performer_pct": best[1] if best else 0,
            "worst_performer_id": worst[0] if worst else None,
            "worst_performer_pct": worst[1] if worst else 0,
        }
