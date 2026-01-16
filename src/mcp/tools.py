"""
Herramientas MCP para Sports Card AI Agent
"""
from typing import Optional, Dict, Any
from datetime import datetime

from src.tools.ebay_tool import EBayTool, EBaySearchParams
from src.agents.price_analyzer_agent import PriceAnalyzerAgent
from src.models.card import Card, Player, Sport, CardCondition, PricePoint


# Instancias globales
ebay_tool = EBayTool()
price_agent = PriceAnalyzerAgent(verbose=False)


async def search_sports_cards(
    keywords: str,
    max_results: int = 10,
    sold_only: bool = False,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> Dict[str, Any]:
    """Busca tarjetas deportivas en eBay"""
    try:
        params = EBaySearchParams(
            keywords=keywords,
            max_results=max_results,
            sold_items_only=sold_only,
            min_price=min_price,
            max_price=max_price
        )
        
        listings = await ebay_tool.search_cards(params)
        
        if not listings:
            return {
                "success": False,
                "message": f"No se encontraron resultados para: {keywords}",
                "results_count": 0,
                "listings": []
            }
        
        formatted_listings = [
            {
                "title": listing.title,
                "price": listing.price,
                "currency": listing.currency,
                "condition": listing.condition,
                "sold": listing.sold,
                "url": listing.listing_url
            }
            for listing in listings
        ]
        
        return {
            "success": True,
            "message": f"Encontrados {len(listings)} resultados",
            "results_count": len(listings),
            "query": keywords,
            "listings": formatted_listings
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "results_count": 0,
            "listings": []
        }


async def analyze_card_investment(
    player_name: str,
    year: int,
    manufacturer: str = "Topps",
    sport: str = "NBA"
) -> Dict[str, Any]:
    """Analiza una tarjeta y genera recomendación"""
    try:
        player = Player(
            id=player_name.lower().replace(" ", "-"),
            name=player_name,
            sport=Sport[sport],
            team="Unknown",
            position="Unknown"
        )
        
        card = Card(
            id=f"{player.id}-{year}",
            player=player,
            year=year,
            manufacturer=manufacturer,
            set_name=f"{manufacturer} Set",
            card_number="Unknown",
            variant="Standard",
            condition=CardCondition.MINT,
            graded=False
        )
        
        # Generar precios de ejemplo
        base_price = 500.0
        prices = []
        
        for i in range(30):
            price_point = PricePoint(
                card_id=card.id,
                price=base_price + (i * 10) + ((-1)**i * 50),
                marketplace="ebay",
                listing_url="https://ebay.com/demo",
                timestamp=datetime.now(),
                sold=True
            )
            prices.append(price_point)
        
        recommendation = price_agent.analyze_card(
            card=card,
            price_history=prices
        )
        
        return {
            "success": True,
            "card": {
                "player": player_name,
                "year": year,
                "manufacturer": manufacturer,
                "sport": sport
            },
            "analysis": {
                "signal": recommendation.signal.value,
                "confidence": round(recommendation.confidence * 100, 1),
                "current_price": recommendation.current_price,
                "reasoning": recommendation.reasoning,
                "factors": recommendation.factors
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def get_player_card_recommendations(
    player_name: str,
    sport: str = "NBA",
    budget: float = 1000.0
) -> Dict[str, Any]:
    """Obtiene recomendaciones de tarjetas"""
    try:
        search_query = f"{player_name} rookie card"
        
        params = EBaySearchParams(
            keywords=search_query,
            max_results=10,
            sold_items_only=True,
            max_price=budget
        )
        
        listings = await ebay_tool.search_cards(params)
        
        if not listings:
            return {
                "success": False,
                "message": f"No se encontraron tarjetas dentro del presupuesto",
                "recommendations": []
            }
        
        recommendations = []
        for listing in listings[:5]:
            value_score = (budget - listing.price) / budget * 100
            
            recommendations.append({
                "title": listing.title,
                "price": listing.price,
                "condition": listing.condition,
                "value_score": round(value_score, 1),
                "url": listing.listing_url
            })
        
        return {
            "success": True,
            "player": player_name,
            "budget": budget,
            "recommendations": recommendations
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def compare_card_prices(
    player_name: str,
    year: int,
    manufacturer: str = "Topps"
) -> Dict[str, Any]:
    """Compara precios entre vendidos y activos"""
    try:
        search_query = f"{player_name} {year} {manufacturer}"
        
        # Items vendidos
        params_sold = EBaySearchParams(
            keywords=search_query,
            max_results=20,
            sold_items_only=True
        )
        sold_listings = await ebay_tool.search_cards(params_sold)
        
        # Items activos
        params_active = EBaySearchParams(
            keywords=search_query,
            max_results=20,
            sold_items_only=False
        )
        active_listings = await ebay_tool.search_cards(params_active)
        
        sold_prices = [l.price for l in sold_listings] if sold_listings else []
        active_prices = [l.price for l in active_listings] if active_listings else []
        
        avg_sold = sum(sold_prices) / len(sold_prices) if sold_prices else 0
        avg_active = sum(active_prices) / len(active_prices) if active_prices else 0
        
        return {
            "success": True,
            "card": f"{player_name} {year} {manufacturer}",
            "sold_items": {
                "count": len(sold_listings),
                "average_price": round(avg_sold, 2)
            },
            "active_items": {
                "count": len(active_listings),
                "average_price": round(avg_active, 2)
            },
            "price_difference_pct": round(((avg_active - avg_sold) / avg_sold * 100), 1) if avg_sold > 0 else 0
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
        
async def multi_agent_analysis(
    player_name: str,
    year: int,
    manufacturer: str = "Topps",
    sport: str = "NBA"
) -> Dict[str, Any]:
    """
    Ejecuta análisis completo con sistema multi-agente
    Coordina Market Research, Player Analysis y Trading Strategy
    
    Args:
        player_name: Nombre del jugador (ej: "Connor McDavid")
        year: Año de la tarjeta (ej: 2015)
        manufacturer: Fabricante (default: "Topps")
        sport: Deporte - "NBA", "NHL" o "MLB" (default: "NBA")
        
    Returns:
        Análisis completo coordinado por el Supervisor Agent
    """
    try:
        from src.agents.supervisor_agent import SupervisorAgent
        
        supervisor = SupervisorAgent()
        
        result = await supervisor.analyze_investment_opportunity(
            player_name=player_name,
            year=year,
            manufacturer=manufacturer,
            sport=sport,
            budget=5000.0
        )
        
        return {
            "success": True,
            "analysis_type": "multi_agent_coordinated",
            "agents_involved": [
                "Market Research Agent",
                "Player Analysis Agent", 
                "Trading Strategy Agent"
            ],
            "card": result["card"],
            "recommendation": {
                "signal": result["recommendation"]["signal"],
                "confidence": f"{result['recommendation']['confidence']:.0%}",
                "current_price": result["recommendation"]["price_targets"]["entry_price"],
                "target_sell": result["recommendation"]["price_targets"]["target_sell_price"],
                "stop_loss": result["recommendation"]["price_targets"]["stop_loss"]
            },
            "market_analysis": {
                "sold_items_count": result["detailed_analysis"]["market"]["market_analysis"]["sold_items"]["count"],
                "average_price": result["detailed_analysis"]["market"]["market_analysis"]["sold_items"]["average_price"],
                "liquidity": result["detailed_analysis"]["market"]["market_analysis"]["liquidity"]
            },
            "player_analysis": {
                "performance_score": result["detailed_analysis"]["player"]["analysis"]["performance_score"]["overall_score"],
                "rating": result["detailed_analysis"]["player"]["analysis"]["performance_score"]["rating"],
                "trend": result["detailed_analysis"]["player"]["analysis"]["performance_score"]["trend"],
                "outlook": result["detailed_analysis"]["player"]["analysis"]["future_outlook"]
            },
            "reasoning": result["reasoning"],
            "action_items": result["action_items"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error executing multi-agent analysis"
        }
    
    