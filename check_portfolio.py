from src.utils.database import get_db
from src.utils.repository import CardRepository

with get_db() as db:
    portfolio = CardRepository.get_portfolio(db)
    print(f"Portfolio items: {len(portfolio)}")
    
    if portfolio:
        print("\nTarjetas en portfolio:")
        for item in portfolio:
            print(f"  - {item['player_name']} {item['year']} ${item['purchase_price']:.2f}")
    else:
        print("Portfolio vacío")