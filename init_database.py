"""
Initialize the database
"""
import sys
import io

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from src.utils.database import init_db, engine, Base
from src.models.db_models import (
    PlayerDB, CardDB, PricePointDB, AnalysisDB,
    PortfolioItemDB, WatchlistDB
)

def main():
    print("="*60)
    print("INITIALIZING DATABASE")
    print("="*60)
    
    print("\nCreating tables...")
    init_db()
    
    print("\nDatabase initialized successfully!")
    print(f"Location: data/sports_cards.db")
    print("\nTables created:")
    print("   - players")
    print("   - cards")
    print("   - price_points")
    print("   - analyses")
    print("   - portfolio_items")
    print("   - watchlist")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()