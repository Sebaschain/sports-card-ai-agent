"""
MCP Server para Sports Card AI Agent
Expone herramientas de análisis de tarjetas deportivas vía Model Context Protocol
"""
import asyncio
import json
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.mcp.tools import (
    search_sports_cards,
    analyze_card_investment,
    get_player_card_recommendations,
    compare_card_prices
)


# Crear instancia del servidor
app = Server("sports-card-ai-agent")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista todas las herramientas disponibles"""
    return [
        Tool(
            name="search_sports_cards",
            description=(
                "Busca tarjetas deportivas en eBay. "
                "Puedes filtrar por precio, deporte, y ver items vendidos o activos."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Palabras clave de búsqueda"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Máximo número de resultados",
                        "default": 10
                    },
                    "sold_only": {
                        "type": "boolean",
                        "description": "Solo mostrar items vendidos",
                        "default": False
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Precio mínimo en USD"
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Precio máximo en USD"
                    }
                },
                "required": ["keywords"]
            }
        ),
        Tool(
            name="analyze_card_investment",
            description=(
                "Analiza una tarjeta deportiva y genera recomendación de inversión"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "player_name": {
                        "type": "string",
                        "description": "Nombre del jugador"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Año de la tarjeta"
                    },
                    "manufacturer": {
                        "type": "string",
                        "description": "Fabricante",
                        "default": "Topps"
                    },
                    "sport": {
                        "type": "string",
                        "enum": ["NBA", "NHL", "MLB"],
                        "default": "NBA"
                    }
                },
                "required": ["player_name", "year"]
            }
        ),
        Tool(
            name="get_player_card_recommendations",
            description="Obtiene recomendaciones de tarjetas para un jugador",
            inputSchema={
                "type": "object",
                "properties": {
                    "player_name": {
                        "type": "string",
                        "description": "Nombre del jugador"
                    },
                    "sport": {
                        "type": "string",
                        "enum": ["NBA", "NHL", "MLB"],
                        "default": "NBA"
                    },
                    "budget": {
                        "type": "number",
                        "description": "Presupuesto máximo en USD",
                        "default": 1000.0
                    }
                },
                "required": ["player_name"]
            }
        ),
        Tool(
            name="compare_card_prices",
            description="Compara precios entre items vendidos y activos",
            inputSchema={
                "type": "object",
                "properties": {
                    "player_name": {
                        "type": "string",
                        "description": "Nombre del jugador"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Año de la tarjeta"
                    },
                    "manufacturer": {
                        "type": "string",
                        "description": "Fabricante",
                        "default": "Topps"
                    }
                },
                "required": ["player_name", "year"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Ejecuta una herramienta"""
    try:
        tool_map = {
            "search_sports_cards": search_sports_cards,
            "analyze_card_investment": analyze_card_investment,
            "get_player_card_recommendations": get_player_card_recommendations,
            "compare_card_prices": compare_card_prices
        }
        
        if name not in tool_map:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Herramienta desconocida: {name}"
                }, indent=2)
            )]
        
        tool_func = tool_map[name]
        result = await tool_func(**arguments)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]


async def main():
    """Inicia el servidor MCP"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())