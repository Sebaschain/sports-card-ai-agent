import sqlite3
import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())


def migrate_auth():
    db_path = "data/sports_cards.db"
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en {db_path}")
        return

    print(f"🔍 Iniciando migración de autenticación en {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Colores para la terminal
        GREEN = "\033[92m"
        END = "\033[0m"

        # 1. Crear tabla 'users'
        print("🛠️ Creando tabla 'users'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✅ Tabla 'users' lista.")

        # 2. Añadir user_id a 'portfolio_items'
        print("🛠️ Añadiendo 'user_id' a 'portfolio_items'...")
        try:
            cursor.execute(
                "ALTER TABLE portfolio_items ADD COLUMN user_id INTEGER REFERENCES users(id)"
            )
            print("  ✅ Columna 'user_id' añadida a 'portfolio_items'.")
        except sqlite3.OperationalError:
            print("  ℹ️ Columna 'user_id' ya existe en 'portfolio_items'.")

        # 3. Añadir user_id a 'watchlist'
        print("🛠️ Añadiendo 'user_id' a 'watchlist'...")
        try:
            cursor.execute(
                "ALTER TABLE watchlist ADD COLUMN user_id INTEGER REFERENCES users(id)"
            )
            print("  ✅ Columna 'user_id' añadida a 'watchlist'.")
        except sqlite3.OperationalError:
            print("  ℹ️ Columna 'user_id' ya existe en 'watchlist'.")

        conn.commit()
        print(f"\n{GREEN}🎉 MIGRACIÓN DE AUTH COMPLETADA!{END}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR DURANTE LA MIGRACIÓN: {str(e)}")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_auth()
