#!/usr/bin/env python3
"""
Script de diagnóstico para eBay API
Ejecuta este script para identificar y solucionar problemas con la API de eBay
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.ebay_tool import EBaySearchParams, EBayTool
from src.utils.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


async def test_ebay_api():
    """Prueba la API de eBay con múltiples métodos"""
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DE EBAY API (Con Fallback y OAuth)")
    print("=" * 60)

    # Verificar configuración
    print("\n1️⃣ CONFIGURACIÓN ACTUAL:")
    print(
        f"   EBAY_APP_ID: {settings.EBAY_APP_ID[:20] if settings.EBAY_APP_ID else 'NO CONFIGURADO'}..."
    )
    print(f"   EBAY_CLIENT_ID: {'CONFIGURADO' if settings.EBAY_CLIENT_ID else 'NO CONFIGURADO'}")
    print(
        f"   EBAY_CLIENT_SECRET: {'CONFIGURADO' if settings.EBAY_CLIENT_SECRET else 'NO CONFIGURADO'}"
    )

    # Inicializar herramienta
    tool = EBayTool()

    # Probar búsqueda con fallback
    print("\n2️⃣ PROBANDO BÚSQUEDA CON FALLBACK:")
    print("   Buscando: 'Luka Doncic card'")

    params = EBaySearchParams(keywords="Luka Doncic card", max_results=5, sold_items_only=False)

    try:
        print("\n⏳ Ejecutando búsqueda con fallback automático...")
        print("   (Intentará: Browse API → Finding API → Scraping)")

        listings = await tool.search_cards(params)

        if listings:
            print(f"\n✅ ÉXITO: Se encontraron {len(listings)} resultados")
            print("\n📦 RESULTADOS:")
            for i, listing in enumerate(listings, 1):
                print(f"   {i}. {listing.title[:60]}...")
                print(f"      Precio: ${listing.price:.2f} {listing.currency}")
                print(f"      Condición: {listing.condition}")
                print()
        else:
            print("\n⚠️ NO SE ENCONTRARON RESULTADOS")
            print("\n📋 PRÓXIMOS PASOS PARA SOLUCIONAR:")
            print("   Opción A - Renovar credenciales eBay:")
            print("      1. Ve a https://developer.ebay.com/")
            print("      2. Inicia sesión con tu cuenta")
            print("      3. Crea o renueva una aplicación")
            print("      4. Obtén EBAY_CLIENT_ID y EBAY_CLIENT_SECRET")
            print("      5. Añádelos al archivo .env")
            print()
            print("   Opción B - El scraping automático debería funcionar")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n🔧 Para solucionarlo:")
        print("   1. Verifica tu conexión a internet")
        print("   2. Confirma que tu App ID está activo en eBay Developer")
        print("   3. Considera usar OAuth en lugar de App ID legacy")


async def test_oauth_only():
    """Prueba específicamente OAuth"""
    print("\n" + "=" * 60)
    print("🔐 PRUEBA DE OAUTH")
    print("=" * 60)

    if not settings.EBAY_CLIENT_ID or not settings.EBAY_CLIENT_SECRET:
        print("\n❌ OAuth no configurado")
        print("   Añade EBAY_CLIENT_ID y EBAY_CLIENT_SECRET al .env")
        return

    tool = EBayTool()
    try:
        print("\n⏳ Solicitando token OAuth...")
        token = await tool._get_oauth_token()
        print(f"✅ Token OAuth obtenido: {token[:20]}...")
        print("\n📋 Próximos pasos:")
        print("   1. Tu OAuth está funcionando")
        print("   2. Ejecuta la búsqueda completa para usar Browse API")
    except Exception as e:
        print(f"\n❌ Error con OAuth: {e}")
        print("\n🔧 Solución:")
        print("   Verifica que EBAY_CLIENT_ID y EBAY_CLIENT_SECRET sean correctos")


if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    # Run tests
    asyncio.run(test_ebay_api())
    asyncio.run(test_oauth_only())
