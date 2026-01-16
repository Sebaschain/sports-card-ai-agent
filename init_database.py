"""
Initialize the database
"""
from src.utils.database import init_db, engine, Base
from src.models.db_models import (
    PlayerDB, CardDB, PricePointDB, AnalysisDB,
    PortfolioItemDB, WatchlistDB
)

def main():
    print("="*60)
    print("🗄️  INITIALIZING DATABASE")
    print("="*60)
    
    print("\n📋 Creating tables...")
    init_db()
    
    print("\n✅ Database initialized successfully!")
    print(f"📍 Location: data/sports_cards.db")
    print("\n📊 Tables created:")
    print("   • players")
    print("   • cards")
    print("   • price_points")
    print("   • analyses")
    print("   • portfolio_items")
    print("   • watchlist")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()