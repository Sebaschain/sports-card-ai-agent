"""
Tests unitarios para OneThirtyPointTool
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.one_thirty_point import (
    AuctionType,
    GradeType,
    OneThirtyPointSale,
    OneThirtyPointSearchParams,
)
from src.tools.one_thirty_point_tool import OneThirtyPointTool


class TestOneThirtyPointTool:
    """Tests para OneThirtyPointTool"""

    @pytest.fixture
    def tool(self):
        """Crea una instancia de la herramienta"""
        return OneThirtyPointTool()

    @pytest.fixture
    def sample_html(self):
        """HTML de ejemplo para testing"""
        return """
        <html>
            <table class="sales-table">
                <tr>
                    <th>Card</th>
                    <th>Price</th>
                    <th>Grade</th>
                    <th>Date</th>
                </tr>
                <tr>
                    <td><a href="/sale/1">2000 Topps LeBron James Chrome Refractor #1</a></td>
                    <td>$500.00</td>
                    <td>PSA 10</td>
                    <td>2024-01-15</td>
                </tr>
                <tr>
                    <td><a href="/sale/2">2000 Topps LeBron James #2</a></td>
                    <td>$450.00</td>
                    <td>PSA 9</td>
                    <td>2024-01-10</td>
                </tr>
            </table>
        </html>
        """

    def test_slugify(self, tool):
        """Test de conversión a slug"""
        assert tool._slugify("LeBron James") == "lebron-james"
        assert tool._slugify("Kevin Durant") == "kevin-durant"
        assert tool._slugify("O'Neal") == "oneal"
        assert tool._slugify("Magic Johnson") == "magic-johnson"

    def test_parse_grade_psa_10(self, tool):
        """Test parsing de PSA 10"""
        value, grade_type = tool._parse_grade("PSA 10")
        assert value == 10.0
        assert grade_type == GradeType.PSA

    def test_parse_grade_bgs_95(self, tool):
        """Test parsing de BGS 9.5"""
        value, grade_type = tool._parse_grade("BGS 9.5")
        assert value == 9.5
        assert grade_type == GradeType.BGS

    def test_parse_grade_sgc(self, tool):
        """Test parsing de SGC"""
        value, grade_type = tool._parse_grade("SGC 10")
        assert value == 10.0
        assert grade_type == GradeType.SGC

    def test_parse_grade_unknown(self, tool):
        """Test parsing de grade desconocido"""
        value, grade_type = tool._parse_grade("UNKNOWN")
        assert value == 0.0
        assert grade_type == GradeType.UNKNOWN

    def test_extract_year(self, tool):
        """Test extracción de año"""
        assert tool._extract_year("2000 Topps LeBron James #1") == 2000
        assert tool._extract_year("1996 Upper Deck Michael Jordan") == 1996
        assert tool._extract_year("No year here") == 2000

    def test_extract_brand(self, tool):
        """Test extracción de marca"""
        assert tool._extract_brand("2000 Topps LeBron James") == "Topps"
        assert tool._extract_brand("2018 Panini Prizm Luka Doncic") == "Panini"
        assert tool._extract_brand("1999 Upper Deck Michael Jordan") == "Upper Deck"
        assert tool._extract_brand("Unknown brand") == "Unknown"

    def test_extract_card_number(self, tool):
        """Test extracción de número de tarjeta"""
        assert tool._extract_card_number("#123") == "123"
        assert tool._extract_card_number("Card #456 Refractor") == "456"
        assert tool._extract_card_number("No number here") is None

    def test_parse_date(self, tool):
        """Test parsing de fechas"""
        # Test formato ISO
        date = tool._parse_date("2024-01-15")
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

        # Test formato US
        date = tool._parse_date("01/15/2024")
        assert date.month == 1
        assert date.day == 15

        # Test formato con mes abreviado
        date = tool._parse_date("Jan 15, 2024")
        assert date.month == 1


class TestOneThirtyPointModels:
    """Tests para modelos de datos"""

    def test_sale_model_valid(self):
        """Test modelo de venta válido"""
        sale = OneThirtyPointSale(
            sale_id="123",
            card_id="card_123",
            player_name="LeBron James",
            year=2000,
            brand="Topps",
            card_number="1",
            grade_raw="PSA 10",
            grade_value=10.0,
            grade_type=GradeType.PSA,
            sale_price=500.0,
            sale_date=datetime.now(),
            auction_url="https://example.com/sale/123",
        )
        assert sale.player_name == "LeBron James"
        assert sale.grade_value == 10.0
        assert sale.sale_price == 500.0

    def test_sale_model_defaults(self):
        """Test valores por defecto"""
        sale = OneThirtyPointSale(
            sale_id="123",
            card_id="card_123",
            player_name="Test",
            year=2000,
            brand="Test",
            card_number="1",
            grade_raw="PSA 10",
            grade_value=10.0,
            grade_type=GradeType.PSA,
            sale_price=100.0,
            sale_date=datetime.now(),
            auction_url=None,
        )
        assert sale.currency == "USD"
        assert sale.auction_type == AuctionType.UNKNOWN
        assert sale.is_rookie_card is False
        assert sale.is_autograph is False

    def test_search_params_defaults(self):
        """Test parámetros de búsqueda por defecto"""
        params = OneThirtyPointSearchParams(player_name="LeBron James")
        assert params.max_results == 50
        assert params.min_price is None
        assert params.max_price is None

    def test_search_params_validation(self):
        """Test validación de parámetros"""
        # max_results debe estar entre 1 y 200
        with pytest.raises(ValueError):
            OneThirtyPointSearchParams(player_name="Test", max_results=300)

        # year debe estar en rango válido
        with pytest.raises(ValueError):
            OneThirtyPointSearchParams(player_name="Test", year=1800)


class TestOneThirtyPointSearchParams:
    """Tests específicos para SearchParams"""

    def test_min_price_validation(self):
        """Test validación de precio mínimo"""
        params = OneThirtyPointSearchParams(player_name="LeBron James", min_price=100.0)
        assert params.min_price == 100.0

    def test_auction_type_filter(self):
        """Test filtro por tipo de subasta"""
        params = OneThirtyPointSearchParams(player_name="Test", auction_type=AuctionType.AUCTION)
        assert params.auction_type == AuctionType.AUCTION


class TestMockedScenarios:
    """Tests con mocks"""

    @pytest.fixture
    def tool_local(self):
        """Crea una instancia de la herramienta"""
        return OneThirtyPointTool()

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, tool_local):
        """Test manejo de rate limit"""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 429

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Too Many Requests", request=MagicMock(), response=mock_response
            )
        )

        with patch.object(tool_local, "_get_client", return_value=mock_client):
            with pytest.raises(Exception):
                await tool_local.search_player_sales("Test Player")
