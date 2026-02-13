"""
Herramienta para interactuar con la API de eBay
Busca tarjetas deportivas y obtiene información de precios
Soporta API Legacy (Finding Service) y API moderna (Browse) con OAuth
"""

import re
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field

from src.utils.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class EBayRateLimitError(Exception):
    """Excepción para cuando se excede el límite de la API de eBay"""

    pass


class EBaySearchParams(BaseModel):
    """Parámetros de búsqueda en eBay"""

    keywords: str = Field(..., description="Palabras clave para buscar")
    category_id: str | None = Field(None, description="ID de categoría de eBay")
    max_results: int = Field(default=10, ge=1, le=100, description="Máximo de resultados")
    sort_order: str = Field(default="BestMatch", description="Orden de resultados")
    sold_items_only: bool = Field(default=False, description="Solo items vendidos")
    min_price: float | None = Field(None, ge=0, description="Precio mínimo")
    max_price: float | None = Field(None, ge=0, description="Precio máximo")


class EBayListing(BaseModel):
    """Representación de un listing de eBay"""

    item_id: str
    title: str
    price: float
    currency: str
    condition: str
    listing_url: str
    image_url: str | None = None
    seller_username: str
    location: str
    sold: bool = False
    end_time: datetime | None = None
    shipping_cost: float | None = None


class EBayTool:
    """
    Herramienta para interactuar con eBay API

    IMPORTANTE:
    - Necesitas credenciales de eBay Developer Program
    - Regístrate en: https://developer.ebay.com/
    - Para OAuth, necesitas un Client ID y Client Secret
    """

    def __init__(self):
        """Inicializa la herramienta de eBay"""
        self.app_id = settings.EBAY_APP_ID
        self.client_id = settings.EBAY_CLIENT_ID  # OAuth Client ID
        self.client_secret = settings.EBAY_CLIENT_SECRET  # OAuth Client Secret
        self.dev_id = settings.EBAY_DEV_ID

        # URLs de las APIs
        self.finding_base_url = "https://svcs.ebay.com/services/search/FindingService/v1"
        self.browse_base_url = "https://api.ebay.com/buy/browse/v1"

        # Categorías de eBay para tarjetas deportivas
        self.categories = {
            "sports_cards": "261328",
            "baseball": "213",
            "basketball": "214",
            "football": "215",
            "hockey": "216",
        }

        # Cache para token OAuth
        self._oauth_token: str | None = None
        self._oauth_expires: datetime | None = None

    async def _get_oauth_token(self) -> str:
        """Obtiene un token de OAuth para la API de Browse"""
        if self._oauth_token and self._oauth_expires and datetime.now() < self._oauth_expires:
            return self._oauth_token

        if not self.client_id or not self.client_secret:
            raise EBayRateLimitError("EBAY_CLIENT_ID y EBAY_CLIENT_SECRET requeridos para OAuth")

        # Solicitar token usando Client Credentials Grant
        auth = (self.client_id, self.client_secret)
        data = {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.ebay.com/oauth/api_token",
                auth=auth,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise EBayRateLimitError(f"Error obteniendo token OAuth: {response.text}")

            token_data = response.json()
            self._oauth_token = token_data["access_token"]
            # El token expira en segundos, restamos 60 segundos para margen de seguridad
            self._oauth_expires = datetime.now() + datetime.timedelta(
                seconds=token_data.get("expires_in", 7200) - 60
            )

            return self._oauth_token

    async def search_cards(self, params: EBaySearchParams) -> list[EBayListing]:
        """
        Busca tarjetas en eBay, intentando primero API moderna con OAuth
        y haciendo fallback a scraping si falla
        """
        if not self.app_id and not self.client_id:
            msg = "EBAY_APP_ID o EBAY_CLIENT_ID no configurado. Regístrate en developer.ebay.com"
            logger.error(msg)
            raise EBayRateLimitError(msg)

        logger.info("[EBAY] === INICIO BÚSQUEDA ===")
        logger.info(f"[EBAY] Keywords: '{params.keywords}'")
        logger.info(f"[EBAY] Sold items only: {params.sold_items_only}")
        logger.info(f"[EBAY] Max results: {params.max_results}")

        # Intentar primero con API Browse (moderna con OAuth)
        if self.client_id and self.client_secret:
            try:
                listings = await self._search_browse_api(params)
                if listings:
                    logger.info(f"[EBAY] Found {len(listings)} listings via Browse API")
                    return listings
            except Exception as e:
                logger.warning(f"[EBAY] Browse API failed: {e}")

        # Intentar con API Legacy (Finding Service)
        if self.app_id:
            try:
                listings = await self._search_finding_api(params)
                if listings:
                    logger.info(f"[EBAY] Found {len(listings)} listings via Finding API")
                    return listings
            except Exception as e:
                logger.warning(f"[EBAY] Finding API failed: {e}")

        # Fallback a scraping
        logger.info("[EBAY] APIs failed, trying web scraping...")
        try:
            listings = await self._scrape_ebay(params.keywords, params.max_results)
            if listings:
                logger.info(f"[EBAY] Found {len(listings)} listings via scraping")
                return listings
        except Exception as e:
            logger.error(f"[EBAY] Scraping also failed: {e}")

        logger.warning("[EBAY] No results from any method")
        return []

    async def _search_browse_api(self, params: EBaySearchParams) -> list[EBayListing]:
        """Busca usando la API moderna de Browse con OAuth"""
        token = await self._get_oauth_token()

        # Construir query
        query = params.keywords
        if params.sold_items_only:
            query += " filter=soldFilter%3Asold"

        if params.max_price:
            query += f" filter=maxPrice%3A{params.max_price}"

        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-ENDUSER-CTX": "contextualLocation=country%3DUS",
        }

        params_url = {
            "q": query,
            "limit": str(params.max_results),
            "sort": "relevance" if params.sort_order == "BestMatch" else params.sort_order,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.browse_base_url}/search",
                params=params_url,
                headers=headers,
            )

            if response.status_code == 429:
                raise EBayRateLimitError("Rate limit exceeded on Browse API")

            if response.status_code != 200:
                logger.error(f"[EBAY] Browse API error: {response.status_code} - {response.text}")
                raise Exception(f"Browse API error: {response.status_code}")

            data = response.json()
            return self._parse_browse_response(data)

    async def _search_finding_api(self, params: EBaySearchParams) -> list[EBayListing]:
        """Busca usando la API Legacy de Finding Service"""
        logger.info(f"[EBAY] Using Finding API with App ID: {self.app_id[:10]}...")

        api_params = {
            "OPERATION-NAME": "findCompletedItems"
            if params.sold_items_only
            else "findItemsAdvanced",
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "GLOBAL-ID": "EBAY-US",
            "keywords": params.keywords,
            "paginationInput.entriesPerPage": params.max_results,
            "sortOrder": params.sort_order,
        }

        if params.category_id:
            api_params["categoryId"] = params.category_id

        if params.min_price:
            api_params["itemFilter(0).name"] = "MinPrice"
            api_params["itemFilter(0).value"] = str(params.min_price)

        if params.max_price:
            api_params["itemFilter(1).name"] = "MaxPrice"
            api_params["itemFilter(1).value"] = str(params.max_price)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.finding_base_url, params=api_params)
            response.raise_for_status()
            data = response.json()

            resp_key = (
                "findCompletedItemsResponse"
                if params.sold_items_only
                else "findItemsAdvancedResponse"
            )

            if resp_key in data:
                ack = data[resp_key][0].get("ack", ["Success"])[0]
                if ack == "Failure":
                    errors = data[resp_key][0].get("errorMessage", [{}])[0].get("error", [])
                    error_msg = (
                        errors[0].get("message", ["Error desconocido"])[0] if errors else "Error"
                    )

                    if any(
                        word in error_msg.lower()
                        for word in ["exceeded", "limit", "authentication", "call usage"]
                    ):
                        raise EBayRateLimitError(f"API Error: {error_msg}")
                    raise Exception(f"eBay API Error: {error_msg}")

            return self._parse_finding_response(data, params.sold_items_only)

    async def _scrape_ebay(self, keywords: str, max_results: int) -> list[EBayListing]:
        """Hace scraping de eBay como último recurso"""
        import bs4

        # URLs alternativas de eBay
        urls_to_try = [
            f"https://www.ebay.com/sch/i.html?_nkw={keywords.replace(' ', '+')}&_sacat=261328",
            f"https://www.ebay.com/sch/i.html?_nkw={keywords.replace(' ', '+')}&rt=nc&_sacat=261328",
            f"https://www.ebay.com/srh?q={keywords.replace(' ', '+')}&catId=261328",
        ]

        for search_url in urls_to_try:
            try:
                logger.info(f"[EBAY] Trying scrape URL: {search_url}")

                # Usar una sesión para manejar cookies y redirects
                async with httpx.AsyncClient(
                    timeout=30.0,
                    follow_redirects=True,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Cache-Control": "max-age=0",
                    },
                ) as client:
                    response = await client.get(search_url)

                    logger.info(
                        f"[EBAY] Scrape response: {response.status_code}, final URL: {response.url}"
                    )

                    if response.status_code != 200:
                        continue

                    soup = bs4.BeautifulSoup(response.text, "html.parser")
                    listings = []

                    # Buscar items con múltiples selectores
                    selectors = [
                        "li.s-item",
                        ".srp-results .s-item",
                        ".s-item",
                        "div.s-item__wrapper",
                    ]

                    items = []
                    for selector in selectors:
                        items = soup.select(selector)
                        if items:
                            logger.info(
                                f"[EBAY] Found {len(items)} items with selector: {selector}"
                            )
                            break

                    for item in items[:max_results]:
                        try:
                            # Múltiples selectores para cada campo
                            title_elem = (
                                item.select_one("h3.s-item__title")
                                or item.select_one(".s-item__title")
                                or item.select_one(".s-item__title-text")
                            )
                            price_elem = item.select_one("span.s-item__price") or item.select_one(
                                ".s-item__price"
                            )
                            link_elem = item.select_one("a.s-item__link") or item.select_one(
                                ".s-item__link"
                            )
                            img_elem = (
                                item.select_one("img.s-item__image-img")
                                or item.select_one(".s-item__image img")
                                or item.select_one("img")
                            )

                            if title_elem and price_elem and link_elem:
                                title = title_elem.get_text(strip=True)
                                if title.lower() in ["skip to main content", "shop by category"]:
                                    continue

                                price_text = price_elem.get_text(strip=True)
                                price_match = re.search(
                                    r"[\d,]+\.?\d*", price_text.replace(",", "")
                                )
                                if price_match:
                                    price = float(price_match.group().replace(",", ""))
                                else:
                                    price = 0.0

                                listing = EBayListing(
                                    item_id="scraped",
                                    title=title,
                                    price=price,
                                    currency="USD",
                                    condition="Unknown",
                                    listing_url=link_elem.get("href", ""),
                                    image_url=img_elem.get("src") if img_elem else None,
                                    seller_username="Unknown",
                                    location="Unknown",
                                    sold=False,
                                )
                                listings.append(listing)

                        except Exception as e:
                            logger.debug(f"[EBAY] Error parsing scraped item: {e}")
                            continue

                    if listings:
                        logger.info(f"[EBAY] Successfully scraped {len(listings)} items")
                        return listings

            except Exception as e:
                logger.debug(f"[EBAY] Error with URL {search_url}: {e}")
                continue

        logger.warning("[EBAY] All scraping attempts failed")
        return []

    def _parse_browse_response(self, data: dict[str, Any]) -> list[EBayListing]:
        """Parsea respuesta de Browse API"""
        listings = []

        items = data.get("itemSummaries", [])

        for item in items:
            try:
                price_info = item.get("price", {})
                price = float(price_info.get("value", 0))
                currency = price_info.get("currency", "USD")

                listing = EBayListing(
                    item_id=item.get("itemId", ""),
                    title=item.get("title", ""),
                    price=price,
                    currency=currency,
                    condition=item.get("condition", "Unknown"),
                    listing_url=item.get("itemWebUrl", ""),
                    image_url=item.get("image", {}).get("imageUrl")
                    if isinstance(item.get("image"), dict)
                    else None,
                    seller_username=item.get("seller", {}).get("username", "Unknown"),
                    location=item.get("itemLocation", {}).get("postalCode", "Unknown"),
                    sold=item.get("buyingOptions", []) == ["FIXED_PRICE"] if False else False,
                    shipping_cost=0.0,
                )
                listings.append(listing)

            except Exception as e:
                logger.debug(f"[EBAY] Error parsing Browse item: {e}")
                continue

        return listings

    def _parse_finding_response(self, data: dict[str, Any], sold_items: bool) -> list[EBayListing]:
        """Parsea respuesta de Finding API (código original)"""
        listings = []

        try:
            resp_key = "findCompletedItemsResponse" if sold_items else "findItemsAdvancedResponse"

            if resp_key not in data:
                return []

            search_result = data[resp_key][0]
            items_container = search_result.get("searchResult", [{}])[0]
            items = items_container.get("item", [])

            for item in items:
                try:
                    item_id = item.get("itemId", [""])[0]
                    title = item.get("title", [""])[0]

                    selling_status = item.get("sellingStatus", [{}])[0]
                    price_info = selling_status.get("currentPrice", [{}])[0]
                    price = float(price_info.get("__value__", 0))
                    currency = price_info.get("@currencyId", "USD")

                    condition_info = item.get("condition", [{}])[0]
                    condition = condition_info.get("conditionDisplayName", ["Unknown"])[0]

                    listing_url = item.get("viewItemURL", [""])[0]
                    image_url = item.get("galleryURL", [""])[0] if "galleryURL" in item else None

                    seller_info = item.get("sellerInfo", [{}])[0]
                    seller_username = seller_info.get("sellerUserName", ["Unknown"])[0]

                    location = item.get("location", ["Unknown"])[0]

                    shipping_info = item.get("shippingInfo", [{}])[0]
                    shipping_cost_info = shipping_info.get("shippingServiceCost", [{}])[0]
                    shipping_cost = (
                        float(shipping_cost_info.get("__value__", 0))
                        if shipping_cost_info
                        else None
                    )

                    listing = EBayListing(
                        item_id=item_id,
                        title=title,
                        price=price,
                        currency=currency,
                        condition=condition,
                        listing_url=listing_url,
                        image_url=image_url,
                        seller_username=seller_username,
                        location=location,
                        sold=sold_items,
                        shipping_cost=shipping_cost,
                    )

                    listings.append(listing)

                except (KeyError, IndexError, ValueError) as e:
                    logger.debug(f"[EBAY] Error parsing Finding item: {e}")
                    continue

        except Exception as e:
            logger.error(f"[EBAY] Error parsing Finding response: {e}")

        return listings

    def build_search_query(
        self,
        player_name: str,
        year: int | None = None,
        manufacturer: str | None = None,
        rookie: bool = False,
        auto: bool = False,
        graded: bool = False,
        psa_grade: int | None = None,
    ) -> str:
        """Construye una query de búsqueda optimizada"""
        query_parts = [player_name]

        if year:
            query_parts.append(str(year))
        if manufacturer:
            query_parts.append(manufacturer)
        if rookie:
            query_parts.append("rookie")
        if auto:
            query_parts.append("auto")
        if graded:
            query_parts.append("PSA" if psa_grade else "graded")
            if psa_grade:
                query_parts.append(str(psa_grade))

        return " ".join(query_parts)


async def search_ebay_cards(
    keywords: str,
    max_results: int = 10,
    sold_only: bool = False,
    min_price: float | None = None,
    max_price: float | None = None,
) -> str:
    """
    Función helper para buscar tarjetas en eBay
    Diseñada para ser usada como tool de LangChain
    """
    tool = EBayTool()
    params = EBaySearchParams(
        keywords=keywords,
        max_results=max_results,
        sold_items_only=sold_only,
        min_price=min_price,
        max_price=max_price,
    )

    listings = await tool.search_cards(params)

    if not listings:
        return f"No se encontraron resultados para: {keywords}"

    result = f"Encontrados {len(listings)} resultados para '{keywords}':\n\n"

    for i, listing in enumerate(listings, 1):
        result += f"{i}. {listing.title}\n"
        result += f"   Precio: ${listing.price:.2f} {listing.currency}\n"
        result += f"   Condición: {listing.condition}\n"
        result += f"   {'VENDIDO' if listing.sold else 'A LA VENTA'}\n"
        result += f"   URL: {listing.listing_url}\n\n"

    return result
