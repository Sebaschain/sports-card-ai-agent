from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """Interfaz base para todas las herramientas del sistema"""

    @property
    @abstractmethod
    def tool_name(self) -> str:
        pass


class BaseMarketTool(BaseTool):
    """Interfaz para herramientas de investigación de mercado"""

    @abstractmethod
    async def get_market_data(
        self, player_name: str, year: int, manufacturer: str
    ) -> Dict[str, Any]:
        """Debe retornar un diccionario estandarizado con precios y tendencias"""
        pass


class BaseStatsTool(BaseTool):
    """Interfaz para herramientas de estadísticas deportistas"""

    @abstractmethod
    async def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """Debe retornar un diccionario estandarizado con rendimiento del jugador"""
        pass
