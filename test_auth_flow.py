from datetime import datetime
from src.utils.database import get_db, init_db
from src.utils.repository import CardRepository
from src.utils.auth_utils import hash_password


def test_auth_and_privacy():
    print("Starting Authentication and Privacy Test...")

    # Initialize DB if needed
    init_db()

    try:
        with get_db() as db:
            # 1. Create two test users
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            user_a_name = f"user_a_{timestamp}"
            user_b_name = f"user_b_{timestamp}"

            print(f"Creating users: {user_a_name}, {user_b_name}")

            user_a = CardRepository.create_user(
                db,
                user_a_name,
                f"{user_a_name}@test.com",
                hash_password("pass_a"),
                "User A",
            )
            user_b = CardRepository.create_user(
                db,
                user_b_name,
                f"{user_b_name}@test.com",
                hash_password("pass_b"),
                "User B",
            )
            db.commit()

            print(f"Users created with IDs: {user_a.id}, {user_b.id}")

            # 2. Add a card for User A
            # First need player and card
            player = CardRepository.get_or_create_player(
                db, "lebron-james-nba", "LeBron James", "NBA"
            )
            card = CardRepository.get_or_create_card(
                db, "lebron-james-nba-2003-topps", player, 2003, "Topps"
            )

            print("Adding card to User A's portfolio...")
            CardRepository.add_to_portfolio(
                db, card, user_a.id, 1000.0, datetime.now(), notes="User A's card"
            )
            db.commit()

            # 3. Verify User A can see their card
            portfolio_a = CardRepository.get_portfolio(db, user_a.id)
            print(f"User A portfolio size: {len(portfolio_a)}")
            assert len(portfolio_a) >= 1, "User A should have at least 1 item"
            assert any(item["notes"] == "User A's card" for item in portfolio_a), (
                "User A card not found"
            )

            # 4. Verify User B CANNOT see User A's card
            portfolio_b = CardRepository.get_portfolio(db, user_b.id)
            print(f"User B portfolio size: {len(portfolio_b)}")
            assert len(portfolio_b) == 0, "User B should have an empty portfolio"

            # 5. Add a card for User B
            print("Adding card to User B's portfolio...")
            CardRepository.add_to_portfolio(
                db, card, user_b.id, 1200.0, datetime.now(), notes="User B's card"
            )
            db.commit()

            # 6. Verify isolation again
            portfolio_a_new = CardRepository.get_portfolio(db, user_a.id)
            portfolio_b_new = CardRepository.get_portfolio(db, user_b.id)

            print(f"User A portfolio size: {len(portfolio_a_new)}")
            print(f"User B portfolio size: {len(portfolio_b_new)}")

            assert all(
                item["notes"] == "User A's card"
                for item in portfolio_a_new
                if item["purchase_price"] == 1000.0
            ), "User A data contaminated"
            assert all(
                item["notes"] == "User B's card"
                for item in portfolio_b_new
                if item["purchase_price"] == 1200.0
            ), "User B data contaminated"

            print("Isolation test passed!")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    if test_auth_and_privacy():
        print("\nALL AUTH TESTS PASSED")
    else:
        print("\nAUTH TESTS FAILED")
