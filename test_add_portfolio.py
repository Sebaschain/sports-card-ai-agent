from datetime import datetime
from src.utils.database import get_db
from src.utils.repository import CardRepository

print("Testing add to portfolio...")

try:
    with get_db() as db:
        # Create player
        player = CardRepository.get_or_create_player(
            db=db,
            player_id="lebron-james-nba",
            name="LeBron James",
            sport="NBA"
        )
        print(f"✅ Player created: {player.name}")
        
        # Create card
        card = CardRepository.get_or_create_card(
            db=db,
            card_id="lebron-james-nba-2003-topps",
            player_db=player,
            year=2003,
            manufacturer="Topps"
        )
        print(f"✅ Card created: {card.year} {card.manufacturer}")
        
        # Add to portfolio
        portfolio_item = CardRepository.add_to_portfolio(
            db=db,
            card=card,
            purchase_price=100.0,
            purchase_date=datetime.now(),
            quantity=1,
            notes="Test card"
        )
        print(f"✅ Added to portfolio: ID {portfolio_item.id}")
        
        # Verify
        portfolio = CardRepository.get_portfolio(db)
        print(f"\n📊 Total items in portfolio: {len(portfolio)}")
        
        for item in portfolio:
            print(f"  - {item['player_name']} ${item['purchase_price']}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()