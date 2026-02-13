"""
Modelos de datos para 130Point
130Point es un sitio de referencia para precios de tarjetas deportivas graded
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class GradeType(str, Enum):
    """Tipos de calificación de tarjetas"""

    PSA = "PSA"
    BGS = "BGS"
    SGC = "SGC"
    CSG = "CSG"
    HGA = "HGA"
    UNKNOWN = "Unknown"


class AuctionType(str, Enum):
    """Tipos de subasta/venta"""

    AUCTION = "auction"
    BUY_IT_NOW = "buy_it_now"
    BEST_OFFER = "best_offer"
    UNKNOWN = "unknown"


class OneThirtyPointSale(BaseModel):
    """
    Representación de una venta en 130Point
    """

    sale_id: str = Field(..., description="ID único de la venta")
    card_id: str = Field(..., description="ID único de la tarjeta")
    player_name: str = Field(..., description="Nombre del jugador")
    year: int = Field(..., ge=1900, le=2030, description="Año de la tarjeta")
    brand: str = Field(..., description="Marca de la tarjeta")
    card_number: str | None = Field(None, description="Número de la tarjeta")
    grade_raw: str = Field(..., description="Calificación original (ej: PSA 10)")
    grade_value: float = Field(..., ge=0, le=10, description="Valor numérico de la calificación")
    grade_type: GradeType = Field(..., description="Tipo de calificación")
    sale_price: float = Field(..., ge=0, description="Precio de venta")
    currency: str = Field(default="USD", description="Moneda")
    sale_date: datetime = Field(..., description="Fecha de la venta")
    auction_type: AuctionType = Field(default=AuctionType.UNKNOWN, description="Tipo de venta")
    auction_url: str | None = Field(None, description="URL de la subasta")
    image_url: str | None = Field(None, description="URL de la imagen de la tarjeta")
    is_rookie_card: bool = Field(default=False, description="Si es tarjeta de rookie")
    is_autograph: bool = Field(default=False, description="Si tiene firma")
    is_patch: bool = Field(default=False, description="Si tiene patch")
    is_parallel: bool = Field(default=False, description="Si es paralela")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class OneThirtyPointSearchParams(BaseModel):
    """Parámetros de búsqueda en 130Point"""

    player_name: str | None = Field(None, description="Nombre del jugador")
    year: int | None = Field(None, ge=1900, le=2030, description="Año de la tarjeta")
    brand: str | None = Field(None, description="Marca de la tarjeta")
    card_number: str | None = Field(None, description="Número de la tarjeta")
    min_grade: str | None = Field(None, description="Calificación mínima")
    max_grade: str | None = Field(None, description="Calificación máxima")
    min_price: float | None = Field(None, ge=0, description="Precio mínimo")
    max_price: float | None = Field(None, ge=0, description="Precio máximo")
    auction_type: AuctionType | None = Field(None, description="Tipo de subasta")
    max_results: int = Field(default=50, ge=1, le=200, description="Máximo de resultados")


class OneThirtyPointPriceSummary(BaseModel):
    """Resumen de precios para una tarjeta"""

    card_id: str
    player_name: str
    year: int
    brand: str
    card_number: str | None
    grade_type: GradeType
    sample_size: int = Field(..., description="Número de ventas en el promedio")
    average_price: float
    median_price: float
    min_price: float
    max_price: float
    standard_deviation: float
    price_trend: str = Field(..., description="up, down, o stable")
    trend_percentage: float = Field(..., description="Porcentaje de cambio de tendencia")
    last_updated: datetime


class OneThirtyPointPlayerPortfolio(BaseModel):
    """Portfolio de ventas de un jugador"""

    player_name: str
    total_sales: int
    total_volume: float
    average_price: float
    top_cards: list[OneThirtyPointSale]
    price_distribution: dict  # grade -> avg_price
