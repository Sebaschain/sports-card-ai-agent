#!/bin/bash
# Production Database Migration Script

set -e

echo "🚀 Starting Production Database Migration..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for database to be ready..."
until pg_isready -h db -p 5432 -U $POSTGRES_USER; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

echo "✅ Database is ready!"

# Run Alembic migrations (if using Alembic)
if [ -f "alembic.ini" ]; then
    echo "🔄 Running Alembic migrations..."
    alembic upgrade head
fi

# Run custom migrations
echo "🔄 Running custom database migrations..."
python scripts/migrate_to_postgres.py

# Create initial data
echo "📊 Creating initial data..."
python scripts/seed_database.py

# Verify database
echo "✅ Verifying database connection..."
python scripts/verify_db.py

echo "✅ Production database migration completed successfully!"