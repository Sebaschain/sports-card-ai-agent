"""
Herramienta para obtener datos históricos de precios de 130Point
130Point es un sitio de referencia para tarjetas deportivas graded

Sitio: https://www.130point.com/
"""

import re
from datetime import datetime, timedelta
from typing import Any

import httpx
from bs4 import BeautifulSoup

from src.models.one_thirty_point import (
    AuctionType,
    GradeType,
    OneThirtyPointPriceSummary,
    OneThirtyPointSale,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class OneThirtyPointRateLimitError(Exception):
    """Excepción para cuando se excede el límite de requests"""

    pass


class OneThirtyPointScrapingError(Exception):
    """Excepción general para errores de scraping"""

    pass


class OneThirtyPointTool:
    """
    Herramienta para obtener datos de precios históricos de 130Point

    NOTA: 130Point no tiene una API pública oficial.
    Esta herramienta utiliza web scraping + parsing de HTML.
    """

    BASE_URL = "https://www.130point.com"
    RATE_LIMIT_DELAY = 2.0  # Segundos entre requests

    def __init__(self):
        """Inicializa la herramienta"""
        self._last_request_time: datetime | None = None
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Obtiene o crea el cliente HTTP síncrono"""
        if self._client is None:
            self._client = httpx.Client(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                },
            )
        return self._client

    def _rate_limit(self):
        """Aplica rate limiting entre requests"""
        if self._last_request_time is not None:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self.RATE_LIMIT_DELAY:
                import time

                time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = datetime.now()

    def search_player_sales(
        self,
        player_name: str,
        year: int | None = None,
        brand: str | None = None,
        max_results: int = 50,
    ) -> list[OneThirtyPointSale]:
        """
        Busca ventas de un jugador específico

        Args:
            player_name: Nombre del jugador
            year: Año opcional de la tarjeta
            brand: Marca opcional
            max_results: Máximo número de resultados

        Returns:
            Lista de ventas encontradas
        """
        self._rate_limit()
        client = self._get_client()

        # Construir URL de búsqueda
        slug = self._slugify(player_name)
        url = f"{self.BASE_URL}/players/{slug}/sales/"

        params = {}
        if year:
            params["year"] = year
        if brand:
            params["brand"] = brand

        try:
            logger.info(f"[130Point] Buscando ventas para: {player_name}")
            logger.info(f"[130Point] URL: {url}")
            response = client.get(url, params=params)
            logger.info(f"[130Point] Response status: {response.status_code}")
            response.raise_for_status()

            sales = self._parse_sales_page(response.text, player_name)
            logger.info(f"[130Point] Encontradas {len(sales)} ventas")

            return sales[:max_results]

        except httpx.HTTPStatusError as e:
            logger.error(f"[130Point] Error HTTP: {e.response.status_code} para URL: {url}")
            if e.response.status_code == 429:
                raise OneThirtyPointRateLimitError("Rate limit excedido")
            elif e.response.status_code == 404:
                raise OneThirtyPointScrapingError(
                    f"HTTP Error 404: No se encontró el jugador '{player_name}' en 130Point. "
                    f"El sitio puede haber cambiado su estructura de URLs o el jugador puede no tener datos disponibles. "
                    f"URL intentada: {url}"
                )
            raise OneThirtyPointScrapingError(f"HTTP Error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"[130Point] Error buscando ventas: {e}")
            raise

    def get_card_price_summary(
        self, player_name: str, year: int, brand: str, card_number: str | None = None
    ) -> OneThirtyPointPriceSummary | None:
        """
        Obtiene resumen de precios para una tarjeta específica

        Args:
            player_name: Nombre del jugador
            year: Año de la tarjeta
            brand: Marca de la tarjeta
            card_number: Número de tarjeta opcional

        Returns:
            Resumen de precios o None si no se encuentra
        """
        self._rate_limit()
        client = self._get_client()

        slug = self._slugify(player_name)
        card_slug = self._slugify(brand)
        url = f"{self.BASE_URL}/players/{slug}/cards/{year}/{card_slug}/"

        if card_number:
            url = f"{url}{card_number}/"

        try:
            logger.info(f"[130Point] Obteniendo precios para: {year} {brand} {player_name}")
            response = client.get(url)
            response.raise_for_status()

            summary = self._parse_price_summary(
                response.text, player_name, year, brand, card_number
            )
            return summary

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_player_portfolio(self, player_name: str, days_back: int = 90) -> dict[str, Any]:
        """
        Obtiene el portfolio completo de ventas de un jugador

        Args:
            player_name: Nombre del jugador
            days_back: Días hacia atrás para las ventas

        Returns:
            Dict con estadísticas del portfolio
        """
        sales = self.search_player_sales(player_name, max_results=200)

        # Filtrar por fecha
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_sales = [s for s in sales if s.sale_date >= cutoff_date]

        # Calcular estadísticas
        if recent_sales:
            prices = [s.sale_price for s in recent_sales]
            total_volume = sum(prices)
            avg_price = total_volume / len(prices)

            # Agrupar por grade
            grade_distribution: dict[str, list[float]] = {}
            for sale in recent_sales:
                grade = sale.grade_raw
                if grade not in grade_distribution:
                    grade_distribution[grade] = []
                grade_distribution[grade].append(sale.sale_price)

            # Calcular promedio por grade
            grade_avg = {
                grade: sum(prices) / len(prices) for grade, prices in grade_distribution.items()
            }

            # Top 5 cartas más vendidas
            top_cards = sorted(recent_sales, key=lambda x: x.sale_price, reverse=True)[:5]
        else:
            total_volume = 0.0
            avg_price = 0.0
            grade_avg = {}
            top_cards = []

        return {
            "player_name": player_name,
            "total_sales": len(recent_sales),
            "total_volume": total_volume,
            "average_price": avg_price,
            "grade_distribution": grade_avg,
            "top_cards": top_cards,
            "days_analyzed": days_back,
        }

    def _slugify(self, text: str) -> str:
        """Convierte texto a formato URL slug"""
        return text.lower().replace(" ", "-").replace("'", "")

    def _parse_sales_page(self, html: str, player_name: str) -> list[OneThirtyPointSale]:
        """
        Parsea una página de ventas de 130Point

        Nota: La estructura exacta del HTML puede variar.
        Ajustar selectores según el HTML real del sitio.
        """
        soup = BeautifulSoup(html, "html.parser")
        sales: list[OneThirtyPointSale] = []

        # Buscar tabla de ventas
        # La estructura típica de 130Point incluye una tabla con filas de ventas
        sales_table = soup.find("table", {"class": "sales-table"}) or soup.find(
            "table", {"id": "sales"}
        )

        if sales_table:
            rows = sales_table.find_all("tr")[1:]  # Skip header
            for row in rows:
                try:
                    sale = self._parse_sale_row(row, player_name)
                    if sale:
                        sales.append(sale)
                except Exception as e:
                    logger.warning(f"[130Point] Error parseando fila: {e}")
                    continue

        # Si no hay tabla, buscar cards grid
        if not sales:
            cards = soup.find_all("div", {"class": "card-sale"})
            for card in cards:
                try:
                    sale = self._parse_sale_card(card, player_name)
                    if sale:
                        sales.append(sale)
                except Exception as e:
                    logger.warning(f"[130Point] Error parseando card: {e}")
                    continue

        return sales

    def _parse_sale_row(self, row, player_name: str) -> OneThirtyPointSale | None:
        """Parsea una fila de la tabla de ventas"""
        cells = row.find_all("td")
        if len(cells) < 5:
            return None

        try:
            # Extraer datos de las celdas
            # Ajustar índices según estructura real del HTML
            title_cell = cells[0]
            price_cell = cells[1]
            grade_cell = cells[2]
            date_cell = cells[3]

            title = title_cell.get_text(strip=True)
            price_text = price_cell.get_text(strip=True)
            grade_text = grade_cell.get_text(strip=True)
            date_text = date_cell.get_text(strip=True)

            # Extraer precio
            price_match = re.search(r"[\$€£]?\s*([\d,]+\.?\d*)", price_text)
            price = float(price_match.group(1).replace(",", "")) if price_match else 0.0

            # Extraer fecha
            sale_date = self._parse_date(date_text)

            # Extraer grade
            grade_value, grade_type = self._parse_grade(grade_text)

            # Extraer link
            link = title_cell.find("a")
            auction_url = link.get("href") if link else None

            # Generar card_id único
            card_id = self._generate_card_id(player_name, title, grade_text)

            return OneThirtyPointSale(
                sale_id=f"130p_{hash(auction_url or title)}",
                card_id=card_id,
                player_name=player_name,
                year=self._extract_year(title),
                brand=self._extract_brand(title),
                card_number=self._extract_card_number(title),
                grade_raw=grade_text,
                grade_value=grade_value,
                grade_type=grade_type,
                sale_price=price,
                sale_date=sale_date,
                auction_url=auction_url,
                auction_type=AuctionType.UNKNOWN,
            )
        except Exception as e:
            logger.warning(f"[130Point] Error en _parse_sale_row: {e}")
            return None

    def _parse_sale_card(self, card, player_name: str) -> OneThirtyPointSale | None:
        """Parsea un card de venta"""
        try:
            title = card.get("data-title", "") or card.find("h3").get_text(strip=True)
            price_text = card.get("data-price", "") or card.find(
                "span", {"class": "price"}
            ).get_text(strip=True)
            grade_text = card.get("data-grade", "") or card.find(
                "span", {"class": "grade"}
            ).get_text(strip=True)

            price_match = re.search(r"[\$€£]?\s*([\d,]+\.?\d*)", price_text)
            price = float(price_match.group(1).replace(",", "")) if price_match else 0.0

            grade_value, grade_type = self._parse_grade(grade_text)
            auction_url = card.find("a").get("href") if card.find("a") else None

            card_id = self._generate_card_id(player_name, title, grade_text)

            return OneThirtyPointSale(
                sale_id=f"130p_{hash(auction_url or title)}",
                card_id=card_id,
                player_name=player_name,
                year=self._extract_year(title),
                brand=self._extract_brand(title),
                card_number=self._extract_card_number(title),
                grade_raw=grade_text,
                grade_value=grade_value,
                grade_type=grade_type,
                sale_price=price,
                sale_date=datetime.now(),
                auction_url=auction_url,
            )
        except Exception as e:
            logger.warning(f"[130Point] Error en _parse_sale_card: {e}")
            return None

    def _parse_price_summary(
        self, html: str, player_name: str, year: int, brand: str, card_number: str | None
    ) -> OneThirtyPointPriceSummary | None:
        """Parsea una página de resumen de precios"""
        soup = BeautifulSoup(html, "html.parser")

        # Buscar estadísticas de precio
        price_elem = soup.find("span", {"class": "average-price"}) or soup.find(
            "div", {"class": "price-summary"}
        )
        if not price_elem:
            return None

        # Extraer datos
        avg_price_text = price_elem.get_text(strip=True)
        avg_price_match = re.search(r"([\d,]+\.?\d*)", avg_price_text.replace(",", ""))
        average_price = float(avg_price_match.group(1)) if avg_price_match else 0.0

        # Determinar tipo de grade
        grade_type = GradeType.PSA
        if "BGS" in html or "Beckett" in html:
            grade_type = GradeType.BGS
        elif "SGC" in html:
            grade_type = GradeType.SGC

        return OneThirtyPointPriceSummary(
            card_id=f"{player_name}_{year}_{brand}_{card_number}",
            player_name=player_name,
            year=year,
            brand=brand,
            card_number=card_number,
            grade_type=grade_type,
            sample_size=1,
            average_price=average_price,
            median_price=average_price,
            min_price=average_price,
            max_price=average_price,
            standard_deviation=0.0,
            price_trend="stable",
            trend_percentage=0.0,
            last_updated=datetime.now(),
        )

    def _parse_grade(self, grade_text: str) -> tuple[float, GradeType]:
        """
        Extrae el valor numérico y tipo de grade
        Ej: "PSA 10" -> (10.0, GradeType.PSA)
             "BGS 9.5" -> (9.5, GradeType.BGS)
        """
        grade_text = grade_text.upper().strip()

        # Determinar tipo
        if "PSA" in grade_text:
            grade_type = GradeType.PSA
        elif "BGS" in grade_text:
            grade_type = GradeType.BGS
        elif "SGC" in grade_text:
            grade_type = GradeType.SGC
        elif "CSG" in grade_text:
            grade_type = GradeType.CSG
        elif "HGA" in grade_text:
            grade_type = GradeType.HGA
        else:
            grade_type = GradeType.UNKNOWN

        # Extraer valor numérico
        match = re.search(r"(\d+\.?\d*)", grade_text)
        if match:
            return float(match.group(1)), grade_type
        return 0.0, grade_type

    def _parse_date(self, date_text: str) -> datetime:
        """Parsea una fecha en various formatos"""
        date_text = date_text.strip()

        # Intentar varios formatos
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%b %d, %Y",
            "%B %d, %Y",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue

        # Si no se puede parsear, usar fecha actual
        logger.warning(f"[130Point] No se pudo parsear fecha: {date_text}")
        return datetime.now()

    def _extract_year(self, title: str) -> int:
        """Extrae el año de un título de tarjeta"""
        match = re.search(r"(19\d{2}|20\d{2})", title)
        if match:
            return int(match.group(1))
        return 2000

    def _extract_brand(self, title: str) -> str:
        """Extrae la marca de un título de tarjeta"""
        brands = ["Topps", "Panini", "Upper Deck", "Fleer", "Donruss", "Score", "Bowman"]
        for brand in brands:
            if brand.lower() in title.lower():
                return brand
        return "Unknown"

    def _extract_card_number(self, title: str) -> str | None:
        """Extrae el número de tarjeta"""
        match = re.search(r"#(\w+)", title)
        if match:
            return match.group(1)
        return None

    def _generate_card_id(self, player_name: str, title: str, grade: str) -> str:
        """Genera un ID único para una tarjeta"""
        year = self._extract_year(title)
        brand = self._extract_brand(title)
        card_num = self._extract_card_number(title) or "0"
        return f"{player_name}_{year}_{brand}_{card_num}_{grade}"


# Función de conveniencia para buscar ventas
def search_130point_sales(
    player_name: str, year: int | None = None, brand: str | None = None, max_results: int = 50
) -> list[OneThirtyPointSale]:
    """
    Busca ventas históricas en 130Point

    Args:
        player_name: Nombre del jugador
        year: Año opcional de la tarjeta
        brand: Marca opcional
        max_results: Máximo de resultados

    Returns:
        Lista de ventas encontradas
    """
    tool = OneThirtyPointTool()
    return tool.search_player_sales(player_name, year, brand, max_results)


# Import necesario para _rate_limit
