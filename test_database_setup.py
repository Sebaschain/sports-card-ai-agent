"""Test database setup"""
print("="*60)
print("Starting database setup test...")
print("="*60)

print("\n1. Testing imports...")
try:
    from src.utils.config import settings
    print("   ✅ Config imported")
except Exception as e:
    print(f"   ❌ Config error: {e}")
    exit(1)

try:
    from src.utils.database import Base, engine, init_db
    print("   ✅ Database utilities imported")
except Exception as e:
    print(f"   ❌ Database error: {e}")
    exit(1)

try:
    from src.models.db_models import PlayerDB, CardDB, AnalysisDB
    print("   ✅ Models imported")
except Exception as e:
    print(f"   ❌ Models error: {e}")
    exit(1)

print("\n2. Checking database path...")
print(f"   📍 Database URL: {settings.DATABASE_URL}")

print("\n3. Creating tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("   ✅ Tables created successfully")
except Exception as e:
    print(f"   ❌ Error creating tables: {e}")
    exit(1)

print("\n4. Verifying tables...")
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"   📊 Tables found: {len(tables)}")
for table in tables:
    print(f"      • {table}")

print("\n" + "="*60)
print("✅ DATABASE SETUP COMPLETE")
print("="*60)