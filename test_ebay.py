"""
Script de prueba para la herramienta de eBay
"""
import asyncio
from src.tools.ebay_tool import EBayTool, EBaySearchParams


async def main():
    print("\n" + "="*60)
    print("🔍 PROBANDO HERRAMIENTA DE EBAY")
    print("="*60 + "\n")
    
    tool = EBayTool()
    
    params = EBaySearchParams(
        keywords="LeBron James rookie card 2003",
        max_results=5,
        sold_items_only=False
    )
    
    print(f"📋 Buscando: {params.keywords}")
    print(f"📊 Máximo de resultados: {params.max_results}")
    print(f"{'='*60}\n")
    
    try:
        listings = await tool.search_cards(params)
        
        if not listings:
            print("❌ No se encontraron resultados\n")
            print("💡 NOTA: Esto es normal si no tienes configurado EBAY_APP_ID")
            print("   Para configurarlo:")
            print("   1. Ve a https://developer.ebay.com/")
            print("   2. Regístrate gratis")
            print("   3. Crea una app y obtén tu App ID")
            print("   4. Añádelo al archivo .env\n")
            return
        
        print(f"✅ Encontrados {len(listings)} resultados:\n")
        
        for i, listing in enumerate(listings, 1):
            print(f"{'─'*60}")
            print(f"📦 Resultado #{i}")
            print(f"{'─'*60}")
            print(f"📌 Título: {listing.title}")
            print(f"💰 Precio: ${listing.price:.2f} {listing.currency}")
            print(f"⭐ Condición: {listing.condition}")
            print(f"📊 Estado: {'✅ VENDIDO' if listing.sold else '🔵 A LA VENTA'}")
            print(f"👤 Vendedor: {listing.seller_username}")
            print(f"📍 Ubicación: {listing.location}")
            if listing.shipping_cost and listing.shipping_cost > 0:
                print(f"🚚 Envío: ${listing.shipping_cost:.2f}")
            print(f"🔗 URL: {listing.listing_url}")
            print()
        
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())