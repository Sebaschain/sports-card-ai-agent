"""Market Research Agent with improved error handling and circuit breaker."""

from datetime import datetime
from typing import Any

from src.tools.ebay_tool import EBayRateLimitError, EBaySearchParams, EBayTool
from src.utils.exceptions import APITemporarilyUnavailableError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CircuitBreaker:
    """Simple circuit breaker for external API calls."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure: datetime | None = None
        self.state = "closed"  # closed, open, half-open

    async def __aenter__(self):
        if self.state == "open":
            if self.last_failure:
                elapsed = (datetime.now() - self.last_failure).total_seconds()
                if elapsed > self.recovery_timeout:
                    self.state = "half-open"
                    logger.info("Circuit breaker: entering half-open state")
                else:
                    raise APITemporarilyUnavailableError(
                        f"Circuit breaker is open. Retry after {self.recovery_timeout - elapsed:.0f}s"
                    )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.failure_count += 1
            self.last_failure = datetime.now()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker: opened after {self.failure_count} failures")
            return False
        else:
            self.failure_count = 0
            if self.state == "half-open":
                self.state = "closed"
                logger.info("Circuit breaker: closed after successful call")
            return True

    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self.state == "open"


class MarketResearchAgent:
    """Agente de investigación de mercado con manejo robusto de errores."""

    def __init__(self):
        self.name = "Market Research Agent"
        self.ebay_tool = EBayTool()
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
        self._price_cache: dict[str, dict[str, Any]] = {}
        self._cache_ttl_seconds = 900  # 15 minutes

    def _get_cached_price(self, search_query: str) -> dict[str, Any] | None:
        """Get cached price data if still valid."""
        if search_query in self._price_cache:
            cached = self._price_cache[search_query]
            elapsed = (datetime.now() - cached["cached_at"]).total_seconds()
            if elapsed < self._cache_ttl_seconds:
                cached["from_cache"] = True
                return cached
        return None

    def _cache_price(self, search_query: str, data: dict[str, Any]) -> None:
        """Cache price data with timestamp."""
        self._price_cache[search_query] = {
            **data,
            "cached_at": datetime.now(),
        }

    async def research_card_market(
        self,
        player_name: str,
        year: int,
        manufacturer: str = "Topps",
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Investiga el mercado de una tarjeta con manejo robusto de errores.

        Args:
            player_name: Nombre del jugador
            year: Año de la tarjeta
            manufacturer: Fabricante de la tarjeta
            use_cache: Si usar cache para evitar llamadas redundantes

        Returns:
            Dict con análisis de mercado
        """
        search_query = f"{player_name} {year} {manufacturer}"
        context_id = f"{datetime.now().isoformat()}_{id(self)}"

        logger.info(
            f"[{context_id}] Researching market for card: {search_query}",
            extra={"context_id": context_id, "search_query": search_query},
        )

        # Try cache first
        if use_cache:
            cached = self._get_cached_price(search_query)
            if cached:
                logger.info(
                    f"[{context_id}] Returning cached data for {search_query}",
                    extra={"context_id": context_id, "cached": True},
                )
                return cached

        sold_listings = []
        try:
            async with self.circuit_breaker:
                sold_params = EBaySearchParams(
                    keywords=search_query,
                    max_results=20,
                    sold_items_only=True,
                )
                sold_listings = await self.ebay_tool.search_cards(sold_params)

        except EBayRateLimitError as e:
            logger.warning(
                f"[{context_id}] eBay rate limit exceeded: {e}",
                extra={"context_id": context_id, "error_type": "rate_limit"},
            )
            return self._create_fallback_response(
                search_query,
                context_id,
                error="Rate limit exceeded. Please try again later.",
            )

        except Exception as e:
            logger.error(
                f"[{context_id}] Error fetching eBay data: {e}",
                exc_info=True,
                extra={"context_id": context_id, "error_type": "api_error"},
            )
            return self._create_fallback_response(
                search_query,
                context_id,
                error=str(e),
            )

        # Process results
        result = self._process_listings(search_query, sold_listings, context_id)

        # Cache the result
        if use_cache:
            self._cache_price(search_query, result)

        return result

    def _process_listings(
        self, search_query: str, listings: list, context_id: str
    ) -> dict[str, Any]:
        """Process listings and calculate statistics."""
        sold_prices = [l.price for l in listings if l.sold]

        if not sold_prices:
            logger.warning(
                f"[{context_id}] No sold listings found for {search_query}",
                extra={"context_id": context_id, "listings_count": 0},
            )
            return self._create_empty_response(search_query, context_id)

        avg_price = sum(sold_prices) / len(sold_prices)
        min_price = min(sold_prices)
        max_price = max(sold_prices)

        # Calculate liquidity based on number of listings
        liquidity = "Baja"
        if len(sold_prices) >= 10:
            liquidity = "Alta"
        elif len(sold_prices) >= 5:
            liquidity = "Media"

        # Calculate price gap percentage
        price_gap = ((max_price - min_price) / avg_price) * 100

        # Generate market insight
        market_insight = self._generate_market_insight(len(sold_prices), avg_price, liquidity)

        return {
            "agent": self.name,
            "card": search_query,
            "timestamp": datetime.now().isoformat(),
            "context_id": context_id,
            "from_cache": False,
            "market_analysis": {
                "sold_items": {
                    "count": len(sold_prices),
                    "average_price": round(avg_price, 2),
                    "min_price": round(min_price, 2),
                    "max_price": round(max_price, 2),
                },
                "active_items": {"count": 0, "average_price": 0},
                "liquidity": liquidity,
                "price_gap_percentage": round(price_gap, 2),
                "market_insight": market_insight,
            },
        }

    def _create_empty_response(self, search_query: str, context_id: str) -> dict[str, Any]:
        """Create response when no listings are found."""
        return {
            "agent": self.name,
            "card": search_query,
            "timestamp": datetime.now().isoformat(),
            "context_id": context_id,
            "from_cache": False,
            "error": "No sales data available",
            "market_analysis": {
                "sold_items": {
                    "count": 0,
                    "average_price": 0.0,
                    "min_price": 0.0,
                    "max_price": 0.0,
                },
                "active_items": {"count": 0, "average_price": 0.0},
                "liquidity": "Desconocida",
                "price_gap_percentage": 0.0,
                "market_insight": "No hay suficientes datos de ventas para analizar.",
            },
        }

    def _create_fallback_response(
        self, search_query: str, context_id: str, error: str
    ) -> dict[str, Any]:
        """Create fallback response when API fails."""
        logger.warning(
            f"[{context_id}] Using fallback response for {search_query}: {error}",
            extra={"context_id": context_id, "error": error},
        )
        return {
            "agent": self.name,
            "card": search_query,
            "timestamp": datetime.now().isoformat(),
            "context_id": context_id,
            "from_cache": False,
            "error": error,
            "market_analysis": {
                "sold_items": {
                    "count": 0,
                    "average_price": 0.0,
                    "min_price": 0.0,
                    "max_price": 0.0,
                },
                "active_items": {"count": 0, "average_price": 0.0},
                "liquidity": "Desconocida",
                "price_gap_percentage": 0.0,
                "market_insight": f"Error al obtener datos: {error}",
            },
        }

    def _generate_market_insight(self, listing_count: int, avg_price: float, liquidity: str) -> str:
        """Generate human-readable market insight."""
        insights = []

        if listing_count < 3:
            insights.append("Datos limitados - precaución al tomar decisiones.")
        elif listing_count >= 10:
            insights.append("Mercado activo con buena muestra de datos.")

        if liquidity == "Alta":
            insights.append("Alta liquidez - fácil encontrar compradores.")
        elif liquidity == "Baja":
            insights.append("Baja liquidez - puede haber dificultad para vender.")

        if avg_price > 1000:
            insights.append("Segmento premium.")
        elif avg_price > 500:
            insights.append("Segmento de precio medio-alto.")
        elif avg_price > 100:
            insights.append("Segmento de precio medio.")
        else:
            insights.append("Segmento económico.")

        return " ".join(insights)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._price_cache),
            "cache_ttl_seconds": self._cache_ttl_seconds,
            "circuit_breaker_state": self.circuit_breaker.state,
            "circuit_breaker_failures": self.circuit_breaker.failure_count,
        }

    def clear_cache(self) -> None:
        """Clear the price cache."""
        self._price_cache.clear()
        logger.info("Price cache cleared")
