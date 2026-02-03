"""
Script to migrate data from SQLite to PostgreSQL
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.db_models import (
    Base,
    UserDB,
    PlayerDB,
    CardDB,
    PricePointDB,
    AnalysisDB,
    PortfolioItemDB,
    WatchlistDB,
    CardImageDB,
)
from src.utils.config import settings


def migrate():
    # SQLite Configuration
    sqlite_url = "sqlite:///./data/sports_cards.db"
    if not os.path.exists("./data/sports_cards.db"):
        print("SQLite database not found at ./data/sports_cards.db")
        return

    sqlite_engine = create_engine(sqlite_url)
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SqliteSession()

    # PostgreSQL Configuration
    pg_url = settings.DATABASE_URL
    if "sqlite" in pg_url:
        print("DATABASE_URL in .env is still pointing to SQLite.")
        return

    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)

    print("Starting migration from SQLite to PostgreSQL...")

    pg_engine = create_engine(pg_url)
    Base.metadata.create_all(bind=pg_engine)
    PgSession = sessionmaker(bind=pg_engine)
    pg_session = PgSession()

    tables = [
        (UserDB, "users"),
        (PlayerDB, "players"),
        (CardDB, "cards"),
        (PricePointDB, "price_points"),
        (AnalysisDB, "analyses"),
        (PortfolioItemDB, "portfolio_items"),
        (WatchlistDB, "watchlist"),
        (CardImageDB, "card_images"),
    ]

    try:
        for model, name in tables:
            print(f"Migrating {name}...")
            items = sqlite_session.query(model).all()
            count = 0
            for item in items:
                sqlite_session.expunge(item)
                from sqlalchemy.orm import make_transient

                make_transient(item)
                pg_session.add(item)
                count += 1

            pg_session.commit()
            print(f"Migrated {count} items from {name}")

        print("\nMigration completed successfully!")

    except Exception as e:
        pg_session.rollback()
        print(f"Error during migration: {e}")
        import traceback

        traceback.print_exc()
    finally:
        sqlite_session.close()
        pg_session.close()


if __name__ == "__main__":
    migrate()
