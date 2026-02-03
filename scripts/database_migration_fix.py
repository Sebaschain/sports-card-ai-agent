"""
Database migration script to fix nullable user_id fields
and ensure data integrity before schema changes.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from src.utils.config import settings


def migrate_user_id_fields():
    """Safely migrate nullable user_id fields to NOT NULL"""

    db_url = settings.DATABASE_URL
    if "sqlite" in db_url:
        engine = create_engine(db_url)
    else:
        engine = create_engine(db_url.replace("postgres://", "postgresql://", 1))

    with engine.connect() as conn:
        print("Checking for orphaned records...")

        # Check orphaned portfolio items
        result = conn.execute(
            text("SELECT COUNT(*) FROM portfolio_items WHERE user_id IS NULL")
        )
        portfolio_orphans = result.scalar()
        print(f"   Portfolio items without user_id: {portfolio_orphans}")

        # Check orphaned watchlist items
        result = conn.execute(
            text("SELECT COUNT(*) FROM watchlist WHERE user_id IS NULL")
        )
        watchlist_orphans = result.scalar()
        print(f"   Watchlist items without user_id: {watchlist_orphans}")

        # Find first user to assign orphaned records
        result = conn.execute(text("SELECT id FROM users ORDER BY id LIMIT 1"))
        first_user = result.scalar()

        if not first_user:
            print("ERROR: No users found in database. Please create a user first.")
            return False

        print(f"   Assigning orphaned records to user_id: {first_user}")

        # Update orphaned portfolio items
        if portfolio_orphans > 0:
            conn.execute(
                text(
                    "UPDATE portfolio_items SET user_id = :user_id WHERE user_id IS NULL"
                ),
                {"user_id": first_user},
            )
            print(f"   SUCCESS: Updated {portfolio_orphans} portfolio items")

        # Update orphaned watchlist items
        if watchlist_orphans > 0:
            conn.execute(
                text("UPDATE watchlist SET user_id = :user_id WHERE user_id IS NULL"),
                {"user_id": first_user},
            )
            print(f"   SUCCESS: Updated {watchlist_orphans} watchlist items")

        conn.commit()

    print("SUCCESS: Migration completed successfully!")
    return True


if __name__ == "__main__":
    success = migrate_user_id_fields()
    sys.exit(0 if success else 1)
