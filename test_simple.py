
"""Test simple de las herramientas"""

print("="*60)
print("🧪 INICIANDO TEST SIMPLE")
print("="*60)

try:
    print("\n1️⃣ Importando módulos...")
    from src.tools.ebay_tool import EBayTool
    print("   ✅ EBayTool importado correctamente")
    
    from src.models.card import Player, Sport
    print("   ✅ Modelos importados correctamente")
    
    from src.utils.config import settings
    print("   ✅ Configuración importada correctamente")
    
    print("\n2️⃣ Creando instancia de EBayTool...")
    tool = EBayTool()
    print("   ✅ Herramienta creada correctamente")
    
    print("\n3️⃣ Verificando configuración...")
    print(f"   📋 Proyecto: {settings.PROJECT_NAME}")
    print(f"   📌 Versión: {settings.VERSION}")
    print(f"   🔑 OpenAI API configurada: {'✅ SÍ' if settings.OPENAI_API_KEY else '❌ NO'}")
    print(f"   🛒 eBay API configurada: {'✅ SÍ' if settings.EBAY_APP_ID else '❌ NO (opcional)'}")
    
    print("\n4️⃣ Probando creación de modelo...")
    player = Player(
        id="test-player",
        name="Test Player",
        sport=Sport.NBA,
        team="Test Team",
        position="Guard"
    )
    print(f"   ✅ Jugador creado: {player.name} ({player.sport})")
    
    print("\n5️⃣ Verificando categorías de eBay...")
    print(f"   📦 Categorías disponibles: {len(tool.categories)}")
    for sport, cat_id in tool.categories.items():
        print(f"      - {sport}: {cat_id}")
    
    print("\n" + "="*60)
    print("✅ TODOS LOS TESTS PASARON CORRECTAMENTE")
    print("="*60)
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Configurar OpenAI API key en .env (para agentes)")
    print("   2. Configurar eBay API key en .env (para búsquedas reales)")
    print("   3. Crear tu primer agente con LangChain")
    print()

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print()