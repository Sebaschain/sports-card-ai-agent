import sys
import os
from sqlalchemy import text

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.database import get_db, db_url
from src.models.db_models import UserDB, PortfolioItemDB, WatchlistDB


def delete_all_users():
    print(f"🌐 Target DB: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    print("🚀 Iniciando limpieza TOTAL de usuarios en producción...")
    try:
        with get_db() as db:
            # Delete dependencies first using explicit DELETE statements for clarity
            print("🗑️ Eliminando items de portfolio...")
            db.query(PortfolioItemDB).delete(synchronize_session=False)

            print("🗑️ Eliminando items de watchlist...")
            db.query(WatchlistDB).delete(synchronize_session=False)

            # Delete users
            print("🗑️ Eliminando todos los usuarios...")
            db.query(UserDB).delete(synchronize_session=False)

            db.commit()
            print("✅ Limpieza completada exitosamente.")

            # Verify immediately
            count = db.query(UserDB).count()
            print(f"📊 Usuarios restantes: {count}")
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")


if __name__ == "__main__":
    delete_all_users()
