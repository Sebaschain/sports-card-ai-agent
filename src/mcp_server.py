import asyncio
import json
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from sqlalchemy.orm import Session

from src.utils.database import get_db_session
from src.utils.repository import CardRepository
from src.tools.ebay_tool import EBayTool, EBaySearchParams
from src.agents.market_research_agent import MarketResearchAgent

# Crear instancia de FastMCP
mcp = FastMCP("Sports Card AI Agent")


@mcp.resource("portfolio://all")
def get_portfolio_resource() -> str:
    """Obtiene el portfolio completo de tarjetas"""
    with get_db_session() as db:
        portfolio = CardRepository.get_portfolio(db)
        return json.dumps(portfolio, indent=2, default=str)


@mcp.resource("portfolio://stats")
def get_portfolio_stats_resource() -> str:
    """Obtiene las estadísticas de rendimiento del portfolio"""
    with get_db_session() as db:
        stats = CardRepository.get_portfolio_stats(db)
        return json.dumps(stats, indent=2, default=str)


@mcp.tool()
async def search_market(query: str, max_results: int = 5) -> str:
    """
    Busca tarjetas en el mercado de eBay para obtener precios actuales.
    """
    tool = EBayTool()
    params = EBaySearchParams(keywords=query, max_results=max_results)
    listings = await tool.search_cards(params)

    if not listings:
        return f"No se encontraron resultados para: {query}"

    output = []
    for l in listings:
        output.append(f"- {l.title}: ${l.price} {l.currency} ({l.condition})")

    return "\n".join(output)


@mcp.tool()
async def analyze_card(player_name: str, year: int, manufacturer: str) -> str:
    """
    Realiza un análisis profundo de inversión para una tarjeta específica.
    """
    from src.agents.supervisor_agent import SupervisorAgent

    supervisor = SupervisorAgent()

    result = await supervisor.analyze_investment_opportunity(
        player_name=player_name, year=year, manufacturer=manufacturer
    )

    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def identify_card_image(image_base64: str) -> str:
    """
    Identifica una tarjeta deportiva a partir de una imagen codificada en base64.
    """
    from src.tools.card_vision_tool import CardVisionTool
    import base64

    vision_tool = CardVisionTool()
    image_bytes = base64.b64decode(image_base64)
    result = await vision_tool.identify_card(image_bytes)

    return json.dumps(result, indent=2, default=str)


if __name__ == "__main__":
    mcp.run()
