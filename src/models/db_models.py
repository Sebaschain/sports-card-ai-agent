"""SQLAlchemy database models"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum

from src.utils.database import Base


class SportEnum(str, enum.Enum):
    NBA = "NBA"
    NHL = "NHL"
    MLB = "MLB"
    NFL = "NFL"
    SOCCER = "SOCCER"


class SignalEnum(str, enum.Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class PlayerDB(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False, index=True)
    sport = Column(SQLEnum(SportEnum), nullable=False)
    team = Column(String)
    position = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    cards = relationship("CardDB", back_populates="player")


class CardDB(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(String, unique=True, index=True, nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    year = Column(Integer, nullable=False, index=True)
    manufacturer = Column(String, nullable=False, index=True)
    set_name = Column(String)
    card_number = Column(String)
    variant = Column(String)
    condition = Column(String)
    is_rookie = Column(Boolean, default=False)
    is_auto = Column(Boolean, default=False)
    is_numbered = Column(Boolean, default=False)
    max_print = Column(Integer)
    sequence_number = Column(Integer)
    graded = Column(Boolean, default=False)
    grade = Column(Float)
    grading_company = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    player = relationship("PlayerDB", back_populates="cards")
    prices = relationship("PricePointDB", back_populates="card")
    analyses = relationship("AnalysisDB", back_populates="card")
    images = relationship("CardImageDB", back_populates="card")


class PricePointDB(Base):
    __tablename__ = "price_points"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    price = Column(Float, nullable=False)
    marketplace = Column(String, nullable=False, index=True)
    listing_url = Column(String)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    sold = Column(Boolean, default=False)
    condition = Column(String)

    card = relationship("CardDB", back_populates="prices")


class AnalysisDB(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    analysis_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    signal = Column(SQLEnum(SignalEnum), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    current_price = Column(Float)
    target_buy_price = Column(Float)
    target_sell_price = Column(Float)
    stop_loss = Column(Float)
    market_avg_price = Column(Float)
    market_liquidity = Column(String)
    market_sold_count = Column(Integer)
    player_score = Column(Integer)
    player_rating = Column(String)
    player_trend = Column(String)
    reasoning = Column(Text)
    factors = Column(Text)
    action_items = Column(Text)

    card = relationship("CardDB", back_populates="analyses")


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    portfolio_items = relationship("PortfolioItemDB", back_populates="user")
    watchlist_items = relationship("WatchlistDB", back_populates="user")


class PortfolioItemDB(Base):
    __tablename__ = "portfolio_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # User ID - required field
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    purchase_price = Column(Float, nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    quantity = Column(Integer, default=1)
    current_value = Column(Float)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    notes = Column(Text)
    image_url_local = Column(String)
    acquisition_source = Column(String)  # eBay, Card Show, Local Store, etc.
    is_active = Column(Boolean, default=True)
    sell_date = Column(DateTime)
    sell_price = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("UserDB", back_populates="portfolio_items")


class WatchlistDB(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # User ID - required field
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    target_buy_price = Column(Float)
    alert_enabled = Column(Boolean, default=True)
    added_date = Column(DateTime, default=datetime.now)
    last_checked = Column(DateTime)
    notes = Column(Text)

    user = relationship("UserDB", back_populates="watchlist_items")


class CardImageDB(Base):
    __tablename__ = "card_images"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    image_url = Column(String, nullable=False)
    image_type = Column(String)  # front, back, corner_detail, etc.
    created_at = Column(DateTime, default=datetime.now)

    card = relationship("CardDB", back_populates="images")
