import sqlite3
import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())


def migrate():
    db_path = "data/sports_cards.db"
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en {db_path}")
        return

    print(f"🔍 Iniciando migración de {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Colores para la terminal
        GREEN = "\033[92m"
        END = "\033[0m"

        # 1. Actualizar tabla 'cards'
        print("🛠️ Actualizando tabla 'cards'...")
        columns_to_add = [
            ("is_rookie", "BOOLEAN DEFAULT 0"),
            ("is_auto", "BOOLEAN DEFAULT 0"),
            ("is_numbered", "BOOLEAN DEFAULT 0"),
            ("max_print", "INTEGER"),
            ("sequence_number", "INTEGER"),
        ]

        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE cards ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ Columna '{col_name}' añadida.")
            except sqlite3.OperationalError:
                print(f"  ℹ️ Columna '{col_name}' ya existe.")

        # 2. Actualizar tabla 'portfolio_items'
        print("🛠️ Actualizando tabla 'portfolio_items'...")
        portfolio_cols = [("image_url_local", "TEXT"), ("acquisition_source", "TEXT")]

        for col_name, col_type in portfolio_cols:
            try:
                cursor.execute(
                    f"ALTER TABLE portfolio_items ADD COLUMN {col_name} {col_type}"
                )
                print(f"  ✅ Columna '{col_name}' añadida.")
            except sqlite3.OperationalError:
                print(f"  ℹ️ Columna '{col_name}' ya existe.")

        # 3. Crear tabla 'card_images'
        print("🛠️ Creando tabla 'card_images'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                image_type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES cards (id)
            )
        """)
        print("  ✅ Tabla 'card_images' lista.")

        conn.commit()
        print(f"\n{GREEN}🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE!{END}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR DURANTE LA MIGRACIÓN: {str(e)}")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
