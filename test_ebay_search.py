import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.tools.ebay_tool import EBayTool, EBaySearchParams
from src.utils.logging_config import setup_logging
import logging


async def test_search():
    setup_logging()
    logger = logging.getLogger("test_ebay")
    logger.setLevel(logging.DEBUG)

    # Force DEBUG level for eBay tool
    logging.getLogger("src.tools.ebay_tool").setLevel(logging.DEBUG)

    tool = EBayTool()
    params = EBaySearchParams(
        keywords="Michael Jordan", max_results=10, sold_items_only=False
    )

    try:
        print(f"Buscando '{params.keywords}'...")
        listings = await tool.search_cards(params)
        print(f"Encontrados: {len(listings)} resultados")

        for i, l in enumerate(listings, 1):
            print(f"{i}. {l.title} - ${l.price}")

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test_search())
