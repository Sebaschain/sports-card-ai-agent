"""
TCGPlayer Tool - API para buscar precios de tarjetas
TCGPlayer es una plataforma major de tarjetas deportivas
"""

import re
from typing import Any

import httpx
from pydantic import BaseModel, Field

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TCGPlayerSearchParams(BaseModel):
    """Parámetros de búsqueda en TCGPlayer"""

    keywords: str = Field(..., description="Palabras clave para buscar")
    category_id: int | None = Field(None, description="ID de categoría")
    max_results: int = Field(default=10, ge=1, le=50, description="Máximo de resultados")
    min_price: float | None = Field(None, ge=0, description="Precio mínimo")
    max_price: float | None = Field(None, ge=0, description="Precio máximo")


class TCGPlayerListing(BaseModel):
    """Representación de un listing de TCGPlayer"""

    product_id: str
    title: str
    price: float
    currency: str = "USD"
    condition: str = "Unknown"
    listing_url: str
    image_url: str | None = None
    seller_username: str
    category: str = "Sports Cards"
    in_stock: bool = True
    quantity_available: int = 1


class TCGPlayerTool:
    """
    Herramienta para buscar tarjetas en TCGPlayer

    TCGPlayer tiene una API pública que no requiere autenticación
    para búsquedas básicas de productos.
    """

    def __init__(self):
        """Inicializa la herramienta de TCGPlayer"""
        self.base_url = "https://api.tcgplayer.com/v1.37.0"
        self.catalog_url = "https://api.tcgplayer.com/catalog/products"
        # Categorías de tarjetas deportivas
        self.categories = {
            "basketball": 123,
            "baseball": 121,
            "football": 122,
            "hockey": 124,
            "soccer": 125,
            "sports": 120,
        }

    async def search_cards(self, params: TCGPlayerSearchParams) -> list[TCGPlayerListing]:
        """Busca tarjetas en TCGPlayer"""
        logger.info(f"[TCG] Searching: '{params.keywords}'")

        try:
            # TCGPlayer API requiere token de acceso para la mayoría de endpoints
            # Pero podemos usar el endpoint público de búsqueda
            search_url = f"{self.base_url}/search"

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Primero intentamos con la API pública
                response = await client.get(
                    search_url,
                    params={
                        "q": params.keywords,
                        "limit": params.max_results,
                    },
                    headers={
                        "Accept": "application/json",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    listings = self._parse_response(data)
                    if listings:
                        logger.info(f"[TCG] Found {len(listings)} listings via API")
                        return listings

                # Si la API falla, intentar con URL pública de scraping
                logger.info("[TCG] API failed, trying public URL...")
                listings = await self._scrape_tcgplayer(params.keywords, params.max_results)
                return listings

        except Exception as e:
            logger.error(f"[TCG] Error searching: {e}")
            # Fallback a scraping
            try:
                listings = await self._scrape_tcgplayer(params.keywords, params.max_results)
                return listings
            except Exception as scrape_error:
                logger.error(f"[TCG] Scraping also failed: {scrape_error}")

        return []

    async def _scrape_tcgplayer(self, keywords: str, max_results: int) -> list[TCGPlayerListing]:
        """Hace scraping público de TCGPlayer"""
        import bs4

        # URL de búsqueda pública
        search_url = f"https://www.tcgplayer.com/search/sports-cards/product?q={keywords.replace(' ', '%20')}"

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                search_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
            )

            if response.status_code != 200:
                logger.warning(f"[TCG] Public URL returned {response.status_code}")
                return []

            soup = bs4.BeautifulSoup(response.text, "html.parser")
            listings = []

            # Buscar cards de productos
            product_cards = soup.select("div.search-result__card, div.product-card")

            logger.info(f"[TCG] Found {len(product_cards)} product cards")

            for card in product_cards[:max_results]:
                try:
                    title_elem = card.select_one(
                        "span.search-result__title, h3.product-card__title"
                    )
                    price_elem = card.select_one(
                        "span.price, span.search-result__price, div.price__value"
                    )
                    link_elem = card.select_one("a.search-result__link, a.product-card__link")
                    img_elem = card.select_one("img.search-result__image, img.product-card__image")

                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        price_text = price_elem.get_text(strip=True) if price_elem else "$0.00"
                        price_match = re.search(r"[\d,]+\.?\d*", price_text.replace(",", ""))
                        price = float(price_match.group().replace(",", "")) if price_match else 0.0

                        listing_url = (
                            f"https://www.tcgplayer.com{link_elem.get('href', '')}"
                            if link_elem
                            else ""
                        )
                        image_url = img_elem.get("src") if img_elem else None

                        listing = TCGPlayerListing(
                            product_id="tcg_scraped",
                            title=title,
                            price=price,
                            listing_url=listing_url,
                            image_url=image_url,
                            seller_username="TCGPlayer Seller",
                        )
                        listings.append(listing)

                except Exception as e:
                    logger.debug(f"[TCG] Error parsing card: {e}")
                    continue

            if not listings:
                # Intentar selectores alternativos
                listings = self._try_alternative_selectors(soup, max_results)

            return listings

    def _try_alternative_selectors(self, soup: Any, max_results: int) -> list[TCGPlayerListing]:
        """Intenta selectores alternativos para TCGPlayer"""
        listings = []

        # Selectores alternativos
        selectors = [
            "li.catalog-product, div.catalog-product",
            "div.result-item, a.result-item",
            "div.product-item, a.product-item",
        ]

        for selector in selectors:
            items = soup.select(selector)
            if items:
                logger.info(f"[TCG] Found {len(items)} items with selector: {selector}")
                break

        for item in items[:max_results]:
            try:
                title_elem = item.select_one("span.name, div.name, h3, .title")
                price_elem = item.select_one("span.price, .price, .value")
                link_elem = item if item.name == "a" else item.select_one("a")

                if title_elem and price_elem:
                    title = title_elem.get_text(strip=True)
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r"[\d,]+\.?\d*", price_text.replace(",", ""))
                    price = float(price_match.group().replace(",", "")) if price_match else 0.0

                    listing = TCGPlayerListing(
                        product_id="tcg_alt",
                        title=title,
                        price=price,
                        listing_url=f"https://www.tcgplayer.com{link_elem.get('href', '')}"
                        if link_elem
                        else "",
                    )
                    listings.append(listing)

            except Exception:
                continue

        return listings

    def _parse_response(self, data: dict[str, Any]) -> list[TCGPlayerListing]:
        """Parsea respuesta de TCGPlayer API"""
        listings = []

        try:
            results = data.get("results", [])
            if not results and "data" in data:
                results = data.get("data", [])

            for item in results:
                try:
                    listing = TCGPlayerListing(
                        product_id=str(item.get("productId", "")),
                        title=item.get("name", ""),
                        price=float(item.get("price", 0)),
                        listing_url=f"https://www.tcgplayer.com/product/{item.get('productId', '')}",
                        image_url=item.get("imageUrl"),
                        seller_username=item.get("sellerUsername", "TCGPlayer"),
                        category=item.get("category", "Sports Cards"),
                    )
                    listings.append(listing)

                except (ValueError, TypeError):
                    continue

        except Exception as e:
            logger.error(f"[TCG] Error parsing API response: {e}")

        return listings

    def build_search_query(
        self,
        player_name: str,
        year: int | None = None,
        manufacturer: str | None = None,
        rookie: bool = False,
        graded: bool = False,
    ) -> str:
        """Construye una query de búsqueda"""
        query_parts = [player_name]

        if year:
            query_parts.append(str(year))
        if manufacturer:
            query_parts.append(manufacturer)
        if rookie:
            query_parts.append("Rookie")
        if graded:
            query_parts.append("PSA")

        return " ".join(query_parts)


async def search_tcgplayer_cards(
    keywords: str,
    max_results: int = 10,
    min_price: float | None = None,
    max_price: float | None = None,
) -> str:
    """Función helper para buscar cartas en TCGPlayer"""
    tool = TCGPlayerTool()
    params = TCGPlayerSearchParams(
        keywords=keywords,
        max_results=max_results,
        min_price=min_price,
        max_price=max_price,
    )

    listings = await tool.search_cards(params)

    if not listings:
        return f"No se encontraron resultados para: {keywords}"

    result = f"Encontrados {len(listings)} resultados en TCGPlayer para '{keywords}':\n\n"

    for i, listing in enumerate(listings, 1):
        result += f"{i}. {listing.title}\n"
        result += f"   Precio: ${listing.price:.2f}\n"
        result += f"   Vendedor: {listing.seller_username}\n"
        result += f"   URL: {listing.listing_url}\n\n"

    return result
