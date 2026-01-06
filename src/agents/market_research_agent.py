"""Market Research Agent"""
from typing import Dict, Any
from datetime import datetime
from src.tools.ebay_tool import EBayTool, EBaySearchParams


class MarketResearchAgent:
    """Agente de investigación de mercado"""
    
    def __init__(self):
        self.name = "Market Research Agent"
        self.ebay_tool = EBayTool()
    
    async def research_card_market(
        self, 
        player_name: str,
        year: int,
        manufacturer: str = "Topps"
    ) -> Dict[str, Any]:
        """Investiga el mercado de una tarjeta"""
        
        search_query = f"{player_name} {year} {manufacturer}"
        
        sold_params = EBaySearchParams(
            keywords=search_query,
            max_results=20,
            sold_items_only=True
        )
        sold_listings = await self.ebay_tool.search_cards(sold_params)
        
        sold_prices = [l.price for l in sold_listings] if sold_listings else []
        avg_sold = sum(sold_prices) / len(sold_prices) if sold_prices else 500.0
        
        return {
            "agent": self.name,
            "card": f"{player_name} {year} {manufacturer}",
            "timestamp": datetime.now().isoformat(),
            "market_analysis": {
                "sold_items": {
                    "count": len(sold_listings),
                    "average_price": round(avg_sold, 2),
                    "min_price": round(min(sold_prices), 2) if sold_prices else 0,
                    "max_price": round(max(sold_prices), 2) if sold_prices else 0
                },
                "active_items": {"count": 0, "average_price": 0},
                "liquidity": "Media",
                "price_gap_percentage": 0,
                "market_insight": "Mercado estable con liquidez moderada"
            }
        }