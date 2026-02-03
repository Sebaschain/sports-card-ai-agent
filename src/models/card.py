from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class Sport(str, Enum):
    """Deportes soportados"""

    NBA = "nba"
    NHL = "nhl"
    MLB = "mlb"
    NFL = "nfl"
    SOCCER = "soccer"


class CardCondition(str, Enum):
    """Condiciones de las tarjetas"""

    MINT = "mint"
    NEAR_MINT = "near_mint"
    EXCELLENT = "excellent"
    VERY_GOOD = "very_good"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class Player(BaseModel):
    """Modelo de jugador"""

    id: str = Field(..., description="ID único del jugador")
    name: str = Field(..., description="Nombre completo del jugador")
    sport: Sport = Field(..., description="Deporte del jugador")
    team: Optional[str] = Field(None, description="Equipo actual")
    position: Optional[str] = Field(None, description="Posición")
    stats_url: Optional[HttpUrl] = Field(None, description="URL a estadísticas")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "lebron-james-nba",
                "name": "LeBron James",
                "sport": "nba",
                "team": "Los Angeles Lakers",
                "position": "Forward",
            }
        }
    }


class Card(BaseModel):
    """Modelo de tarjeta deportiva"""

    id: str = Field(..., description="ID único de la tarjeta")
    player: Player = Field(..., description="Información del jugador")
    year: int = Field(..., ge=1900, le=2100, description="Año de la tarjeta")
    manufacturer: str = Field(..., description="Fabricante (Topps, Panini, etc.)")
    set_name: str = Field(..., description="Nombre del set")
    card_number: str = Field(..., description="Número de la tarjeta")
    variant: Optional[str] = Field(None, description="Variante (rookie, auto, etc.)")
    condition: CardCondition = Field(..., description="Condición de la tarjeta")
    graded: bool = Field(default=False, description="Si está graduada")
    grade: Optional[float] = Field(None, ge=1, le=10, description="Grado (PSA, BGS)")
    grading_company: Optional[str] = Field(None, description="Compañía de graduación")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "lebron-2003-topps-221",
                "year": 2003,
                "manufacturer": "Topps",
                "set_name": "Topps Chrome",
                "card_number": "221",
                "variant": "Rookie Card",
                "condition": "mint",
                "graded": True,
                "grade": 9.5,
                "grading_company": "PSA",
            }
        }
    }


class PricePoint(BaseModel):
    """Punto de precio en el tiempo"""

    card_id: str = Field(..., description="ID de la tarjeta")
    price: float = Field(..., gt=0, description="Precio en USD")
    marketplace: str = Field(..., description="Marketplace (eBay, COMC, etc.)")
    listing_url: Optional[HttpUrl] = Field(None, description="URL del listing")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Fecha del precio"
    )
    sold: bool = Field(default=False, description="Si se vendió o solo es un listing")

    model_config = {
        "json_schema_extra": {
            "example": {
                "card_id": "lebron-2003-topps-221",
                "price": 1250.00,
                "marketplace": "ebay",
                "sold": True,
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }
    }


class PriceHistory(BaseModel):
    """Historial de precios de una tarjeta"""

    card: Card = Field(..., description="Información de la tarjeta")
    prices: List[PricePoint] = Field(
        default_factory=list, description="Lista de precios"
    )

    @property
    def current_price(self) -> Optional[float]:
        """Precio más reciente"""
        if not self.prices:
            return None
        return sorted(self.prices, key=lambda x: x.timestamp, reverse=True)[0].price

    @property
    def average_price(self) -> Optional[float]:
        """Precio promedio"""
        if not self.prices:
            return None
        return sum(p.price for p in self.prices) / len(self.prices)


class PlayerStats(BaseModel):
    """Estadísticas actuales de un jugador"""

    player_id: str = Field(..., description="ID del jugador")
    season: str = Field(..., description="Temporada (ej: 2024-25)")
    games_played: int = Field(..., ge=0)
    points_per_game: Optional[float] = Field(None, ge=0)
    assists_per_game: Optional[float] = Field(None, ge=0)
    rebounds_per_game: Optional[float] = Field(None, ge=0)
    recent_performance: str = Field(
        ..., description="Descripción de rendimiento reciente"
    )
    injuries: List[str] = Field(default_factory=list, description="Lesiones actuales")
    team_standing: Optional[str] = Field(None, description="Posición del equipo")

    model_config = {
        "json_schema_extra": {
            "example": {
                "player_id": "lebron-james-nba",
                "season": "2024-25",
                "games_played": 45,
                "points_per_game": 25.3,
                "assists_per_game": 7.8,
                "rebounds_per_game": 7.2,
                "recent_performance": "Hot streak - 30+ points in last 3 games",
                "injuries": [],
                "team_standing": "7th in Western Conference",
            }
        }
    }


class TradingSignal(str, Enum):
    """Señales de trading"""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class TradingRecommendation(BaseModel):
    """Recomendación de trading generada por el agente"""

    card: Card = Field(..., description="Tarjeta analizada")
    signal: TradingSignal = Field(..., description="Señal de trading")
    confidence: float = Field(..., ge=0, le=1, description="Confianza (0-1)")
    current_price: float = Field(..., gt=0, description="Precio actual")
    target_buy_price: Optional[float] = Field(
        None, description="Precio objetivo de compra"
    )
    target_sell_price: Optional[float] = Field(
        None, description="Precio objetivo de venta"
    )
    reasoning: str = Field(..., description="Razonamiento de la recomendación")
    factors: List[str] = Field(..., description="Factores considerados")
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "example": {
                "signal": "buy",
                "confidence": 0.85,
                "current_price": 1200.00,
                "target_buy_price": 1150.00,
                "target_sell_price": 1500.00,
                "reasoning": "El jugador está en racha caliente y el precio está por debajo del promedio de 30 días",
                "factors": [
                    "Rendimiento reciente excepcional",
                    "Precio 15% bajo el promedio mensual",
                    "Alta demanda en el mercado",
                ],
            }
        }
    }
