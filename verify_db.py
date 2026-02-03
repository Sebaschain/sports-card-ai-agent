"""
Script de verificación de conexión a la base de datos (PostgreSQL/SQLite)
"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from src.utils.database import engine, init_db, get_db
from sqlalchemy import text


def verify_connection():
    print("=" * 60)
    print("📋 VERIFICACIÓN DE BASE DE DATOS")
    print("=" * 60)

    try:
        # 1. Probar conexión física
        print(f"🔗 Intentando conectar a: {engine.url}")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Conexión exitosa!")

        # 2. Inicializar tablas
        print("\n🛠️ Inicializando tablas...")
        init_db()

        # 3. Verificar tablas creadas
        with engine.connect() as conn:
            from sqlalchemy import inspect

            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"✅ Tablas encontradas ({len(tables)}): {', '.join(tables)}")

        print("\n" + "=" * 60)
        print("🎉 TODO LISTO: La base de datos está configurada correctamente.")
        print("=" * 60)

    except Exception as e:
        print("\n" + "!" * 60)
        print("❌ ERROR DE CONEXIÓN")
        print("!" * 60)
        print(f"\nDetalle: {str(e)}")
        print("\n💡 Sugerencias:")
        if "postgresql" in str(engine.url):
            print(
                "1. ¿Está corriendo el contenedor de Docker? (docker compose up -d db)"
            )
            print(
                "2. ¿Las credenciales en el archivo .env coinciden con docker-compose.yml?"
            )
            print("3. ¿El puerto 5432 está libre?")
        print("=" * 60)


if __name__ == "__main__":
    verify_connection()
