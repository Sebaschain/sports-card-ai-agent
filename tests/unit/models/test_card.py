"""Tests for Card and Player data models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.card import Card, CardCondition, Player, PricePoint, Sport


class TestSportEnum:
    """Test cases for Sport enum."""

    def test_sport_values(self) -> None:
        """Test that all sports are defined correctly."""
        assert Sport.NBA.value == "nba"
        assert Sport.NHL.value == "nhl"
        assert Sport.MLB.value == "mlb"
        assert Sport.NFL.value == "nfl"
        assert Sport.SOCCER.value == "soccer"

    def test_sport_from_string(self) -> None:
        """Test creating Sport enum from string."""
        # Sport enum uses lowercase values
        assert Sport("nba") == Sport.NBA
        assert Sport("nhl") == Sport.NHL


class TestCardConditionEnum:
    """Test cases for CardCondition enum."""

    def test_condition_values(self) -> None:
        """Test that all conditions are defined correctly."""
        assert CardCondition.MINT.value == "mint"
        assert CardCondition.NEAR_MINT.value == "near_mint"
        assert CardCondition.EXCELLENT.value == "excellent"
        assert CardCondition.VERY_GOOD.value == "very_good"
        assert CardCondition.GOOD.value == "good"
        assert CardCondition.FAIR.value == "fair"
        assert CardCondition.POOR.value == "poor"


class TestPlayerModel:
    """Test cases for Player model."""

    def test_player_creation_minimal(self) -> None:
        """Test creating a Player with minimal fields."""
        player = Player(
            id="lebron-james-nba",
            name="LeBron James",
            sport=Sport.NBA,
        )
        assert player.id == "lebron-james-nba"
        assert player.name == "LeBron James"
        assert player.sport == Sport.NBA

    def test_player_creation_full(self) -> None:
        """Test creating a Player with all fields."""
        player = Player(
            id="lebron-james-nba",
            name="LeBron James",
            sport=Sport.NBA,
            team="Los Angeles Lakers",
            position="Forward",
        )
        assert player.team == "Los Angeles Lakers"
        assert player.position == "Forward"

    def test_player_json_schema(self) -> None:
        """Test Player model JSON schema."""
        schema = Player.model_json_schema()
        assert schema["properties"]["id"]["description"] == "ID único del jugador"
        assert schema["properties"]["name"]["description"] == "Nombre completo del jugador"


class TestCardModel:
    """Test cases for Card model."""

    @pytest.fixture
    def sample_player(self) -> Player:
        """Create a sample player."""
        return Player(
            id="lebron-james-nba",
            name="LeBron James",
            sport=Sport.NBA,
            team="Los Angeles Lakers",
            position="Forward",
        )

    def test_card_creation_minimal(
        self,
        sample_player: Player,
    ) -> None:
        """Test creating a Card with minimal fields."""
        card = Card(
            id="lebron-2003-topps-221",
            player=sample_player,
            year=2003,
            manufacturer="Topps",
            set_name="Topps Chrome",
            card_number="221",
            condition=CardCondition.MINT,
        )
        assert card.id == "lebron-2003-topps-221"
        assert card.year == 2003
        assert card.manufacturer == "Topps"

    def test_card_creation_full(
        self,
        sample_player: Player,
    ) -> None:
        """Test creating a Card with all fields."""
        card = Card(
            id="lebron-2003-topps-221",
            player=sample_player,
            year=2003,
            manufacturer="Topps",
            set_name="Topps Chrome",
            card_number="221",
            variant="Rookie Card",
            condition=CardCondition.MINT,
            graded=True,
            grade=9.5,
            grading_company="PSA",
        )
        assert card.variant == "Rookie Card"
        assert card.graded is True
        assert card.grade == 9.5
        assert card.grading_company == "PSA"

    def test_card_year_validation(
        self,
        sample_player: Player,
    ) -> None:
        """Test Card year validation."""
        # Valid year
        card = Card(
            id="test",
            player=sample_player,
            year=2003,
            manufacturer="Topps",
            set_name="Test",
            card_number="1",
            condition=CardCondition.MINT,
        )
        assert card.year == 2003

        # Invalid year (too low)
        with pytest.raises(ValidationError):
            Card(
                id="test",
                player=sample_player,
                year=1800,
                manufacturer="Topps",
                set_name="Test",
                card_number="1",
                condition=CardCondition.MINT,
            )

        # Invalid year (too high)
        with pytest.raises(ValidationError):
            Card(
                id="test",
                player=sample_player,
                year=2200,
                manufacturer="Topps",
                set_name="Test",
                card_number="1",
                condition=CardCondition.MINT,
            )

    def test_card_grade_validation(
        self,
        sample_player: Player,
    ) -> None:
        """Test Card grade validation."""
        # Valid grade
        card = Card(
            id="test",
            player=sample_player,
            year=2003,
            manufacturer="Topps",
            set_name="Test",
            card_number="1",
            condition=CardCondition.MINT,
            graded=True,
            grade=10.0,
        )
        assert card.grade == 10.0

        # Invalid grade (too high)
        with pytest.raises(ValidationError):
            Card(
                id="test",
                player=sample_player,
                year=2003,
                manufacturer="Topps",
                set_name="Test",
                card_number="1",
                condition=CardCondition.MINT,
                graded=True,
                grade=10.5,
            )


class TestPricePointModel:
    """Test cases for PricePoint model."""

    def test_price_point_creation(self) -> None:
        """Test creating a PricePoint."""
        price_point = PricePoint(
            card_id="lebron-2003-topps-221",
            price=599.99,
            marketplace="eBay",
            listing_url="https://ebay.com/itm/12345",
            sold=True,
        )
        assert price_point.card_id == "lebron-2003-topps-221"
        assert price_point.price == 599.99
        assert price_point.marketplace == "eBay"
        assert price_point.sold is True

    def test_price_point_default_values(self) -> None:
        """Test PricePoint default values."""
        price_point = PricePoint(
            card_id="test",
            price=100.0,
            marketplace="eBay",
        )
        assert price_point.sold is False
        assert price_point.listing_url is None
        assert isinstance(price_point.timestamp, datetime)

    def test_price_validation(self) -> None:
        """Test PricePoint price validation."""
        # Valid price
        price_point = PricePoint(
            card_id="test",
            price=0.01,
            marketplace="eBay",
        )
        assert price_point.price > 0

        # Invalid price (zero)
        with pytest.raises(ValidationError):
            PricePoint(
                card_id="test",
                price=0,
                marketplace="eBay",
            )

        # Invalid price (negative)
        with pytest.raises(ValidationError):
            PricePoint(
                card_id="test",
                price=-100.0,
                marketplace="eBay",
            )
