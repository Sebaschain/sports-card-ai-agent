
"""
Herramienta para interactuar con la API de eBay
Busca tarjetas deportivas y obtiene información de precios
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from pydantic import BaseModel, Field

from src.utils.config import settings
from src.models.card import PricePoint


class EBaySearchParams(BaseModel):
    """Parámetros de búsqueda en eBay"""
    keywords: str = Field(..., description="Palabras clave para buscar")
    category_id: Optional[str] = Field(None, description="ID de categoría de eBay")
    max_results: int = Field(default=10, ge=1, le=100, description="Máximo de resultados")
    sort_order: str = Field(default="BestMatch", description="Orden de resultados")
    sold_items_only: bool = Field(default=False, description="Solo items vendidos")
    min_price: Optional[float] = Field(None, ge=0, description="Precio mínimo")
    max_price: Optional[float] = Field(None, ge=0, description="Precio máximo")


class EBayListing(BaseModel):
    """Representación de un listing de eBay"""
    item_id: str
    title: str
    price: float
    currency: str
    condition: str
    listing_url: str
    image_url: Optional[str] = None
    seller_username: str
    location: str
    sold: bool = False
    end_time: Optional[datetime] = None
    shipping_cost: Optional[float] = None


class EBayTool:
    """
    Herramienta para interactuar con eBay API
    
    IMPORTANTE: 
    - Necesitas credenciales de eBay Developer Program
    - Regístrate en: https://developer.ebay.com/
    """
    
    def __init__(self):
        """Inicializa la herramienta de eBay"""
        self.app_id = settings.EBAY_APP_ID
        self.base_url = "https://svcs.ebay.com/services/search/FindingService/v1"
        
        # Categorías de eBay para tarjetas deportivas
        self.categories = {
            "sports_cards": "261328",
            "baseball": "213",
            "basketball": "214",
            "football": "215",
            "hockey": "216",
        }
    
    async def search_cards(self, params: EBaySearchParams) -> List[EBayListing]:
        """Busca tarjetas en eBay"""
        if not self.app_id:
            print("\n⚠️  eBay App ID no configurado")
            print("Para usar esta función necesitas:")
            print("1. Ir a https://developer.ebay.com/")
            print("2. Crear una cuenta gratuita")
            print("3. Crear una aplicación y obtener tu App ID")
            print("4. Añadirlo al archivo .env como EBAY_APP_ID\n")
            return []
        
        # Construir parámetros de la API
        api_params = {
            "OPERATION-NAME": "findCompletedItems" if params.sold_items_only else "findItemsAdvanced",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "keywords": params.keywords,
            "paginationInput.entriesPerPage": params.max_results,
            "sortOrder": params.sort_order,
        }
        
        # Añadir categoría si existe
        if params.category_id:
            api_params["categoryId"] = params.category_id
        
        # Añadir filtros de precio
        filter_index = 0
        if params.min_price is not None:
            api_params[f"itemFilter({filter_index}).name"] = "MinPrice"
            api_params[f"itemFilter({filter_index}).value"] = str(params.min_price)
            filter_index += 1
        
        if params.max_price is not None:
            api_params[f"itemFilter({filter_index}).name"] = "MaxPrice"
            api_params[f"itemFilter({filter_index}).value"] = str(params.max_price)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=api_params)
                response.raise_for_status()
                data = response.json()
                
                return self._parse_response(data, params.sold_items_only)
        
        except httpx.HTTPError as e:
            print(f"❌ Error al buscar en eBay: {e}")
            return []
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return []
    
    def _parse_response(self, data: Dict[str, Any], sold_items: bool) -> List[EBayListing]:
        """Parsea la respuesta de eBay API"""
        listings = []
        
        try:
            search_result = data.get(
                "findCompletedItemsResponse" if sold_items else "findItemsAdvancedResponse", 
                [{}]
            )[0]
            items = search_result.get("searchResult", [{}])[0].get("item", [])
            
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
                    shipping_cost = float(shipping_cost_info.get("__value__", 0)) if shipping_cost_info else None
                    
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
                        shipping_cost=shipping_cost
                    )
                    
                    listings.append(listing)
                
                except (KeyError, IndexError, ValueError):
                    continue
        
        except Exception as e:
            print(f"❌ Error parseando respuesta de eBay: {e}")
        
        return listings
    
    def build_search_query(
        self,
        player_name: str,
        year: Optional[int] = None,
        manufacturer: Optional[str] = None,
        rookie: bool = False,
        auto: bool = False,
        graded: bool = False,
        psa_grade: Optional[int] = None
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
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
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
        max_price=max_price
    )
    
    listings = await tool.search_cards(params)
    
    if not listings:
        return f"No se encontraron resultados para: {keywords}"
    
    result = f"Encontrados {len(listings)} resultados para '{keywords}':\n\n"
    
    for i, listing in enumerate(listings, 1):
        result += f"{i}. {listing.title}\n"
        result += f"   Precio: ${listing.price:.2f} {listing.currency}\n"
        result += f"   Condición: {listing.condition}\n"
        result += f"   {'✅ VENDIDO' if listing.sold else '🔵 A LA VENTA'}\n"
        result += f"   URL: {listing.listing_url}\n\n"
    
    return result