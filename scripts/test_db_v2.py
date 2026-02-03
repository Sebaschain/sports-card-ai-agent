from sqlalchemy.orm import Session
from src.utils.database import get_db
from src.utils.repository import CardRepository
from src.models.db_models import CardDB, PortfolioItemDB
from datetime import datetime


def verify_v2_features():
    print("🧪 Verificando nuevas características de BD v2 + Auth...")

    with get_db() as db:
        # 0. Crear usuario de prueba
        print("👤 Verificando usuario de prueba...")
        user = CardRepository.get_user_by_username(db, "testuser_v2")
        if not user:
            user = CardRepository.create_user(
                db, "testuser_v2", "test2@example.com", "hash", "Test User V2"
            )
            db.commit()
            print("  ✅ Usuario de prueba creado.")

        # 1. Probar guardado de tarjeta con rareza
        print("📝 Probando guardado de tarjeta numerada...")
        player = CardRepository.get_or_create_player(
            db, "test-player-v2-auth", "Test Player V2 Auth", "NBA"
        )

        card = CardRepository.get_or_create_card(
            db,
            "test-card-v3-auth",
            player,
            2024,
            "Panini",
            is_rookie=True,
            is_numbered=True,
            max_print=99,
            sequence_number=1,
        )

        db.commit()

        # 2. Verificar datos guardados
        db.refresh(card)
        if card.is_rookie and card.is_numbered and card.max_print == 99:
            print("  ✅ Tarjeta guardada correctamente con nuevos campos.")
        else:
            print("  ❌ Falló la verificación de campos de rareza.")

        # 3. Probar Portfolio con Auth y origen
        print("📝 Probando item de portfolio con Auth y fuente de adquisición...")
        p_item = CardRepository.add_to_portfolio(
            db=db,
            card=card,
            user_id=user.id,
            purchase_price=50.0,
            purchase_date=datetime.now(),
            acquisition_source="eBay",
        )
        db.commit()
        db.refresh(p_item)

        if p_item.acquisition_source == "eBay" and p_item.user_id == user.id:
            print("  ✅ Item de portfolio guardado con éxito (Auth OK).")
        else:
            print(f"  ❌ Falló la verificación. UserID: {p_item.user_id}")


if __name__ == "__main__":
    try:
        verify_v2_features()
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
