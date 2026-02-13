"""
Script de verificación para datos en tiempo real y syncing
"""

import asyncio
from src.tools.nhl_stats_tool import NHLStatsTool
from src.utils.realtime_sync import RealtimeSync
from src.utils.logging_config import setup_logging


async def verify_real_time():
    setup_logging()

    # 1. Verificar NHL Real API
    print("\n--- Verificando NHL Real API ---")
    nhl_tool = NHLStatsTool()
    # Connor McDavid (ID: 8478402)
    stats = await nhl_tool.get_player_stats("Connor McDavid")

    if stats.get("success") and not stats.get("simulated"):
        print(f"✅ Éxito: Datos reales obtenidos para {stats['player_name']}")
        print(f"   Equipo: {stats['team']}, G: {stats['goals']}, A: {stats['assists']}")
    else:
        print(f"❌ Error: Se obtuvieron datos simulados o falló la API para NHL")

    # 2. Verificar Sync de Portfolio (requiere un usuario con ID 1 o similar en la DB)
    print("\n--- Verificando RealtimeSync ---")
    sync = RealtimeSync()
    try:
        # Intentamos sincronizar para el usuario 1 (ajustar si es necesario)
        results = await sync.sync_portfolio(user_id=1)
        print(
            f"✅ Sync completado: {results['updated']} items actualizados, {results['errors']} errores"
        )
    except Exception as e:
        print(
            f"⚠️ Nota: El sync falló o no hay usuario 1, esto es normal si la DB está vacía: {e}"
        )


if __name__ == "__main__":
    asyncio.run(verify_real_time())
