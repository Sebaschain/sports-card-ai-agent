import asyncio
import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from src.tools.card_vision_tool import CardVisionTool


async def test_vision(image_path):
    print(f"📷 Probando Vision AI con: {image_path}")

    if not os.path.exists(image_path):
        print("❌ Error: El archivo de imagen no existe.")
        return

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    vision_tool = CardVisionTool()
    print("🤖 Analizando...")
    result = await vision_tool.identify_card(image_bytes)

    if result.get("success"):
        print("\n✅ Tarjeta Identificada:")
        print(f"   Jugador: {result.get('player_name')}")
        print(f"   Año: {result.get('year')}")
        print(f"   Fabricante: {result.get('manufacturer')}")
        print(f"   Set: {result.get('set_name')}")
        print(f"   Variante: {result.get('variant')}")
        print(f"   Grado: {result.get('grade')} ({result.get('grading_company')})")
        print(f"   Confianza: {result.get('confidence'):.0%}")
    else:
        print(f"❌ Error: {result.get('error')}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_vision.py <ruta_a_la_imagen>")
    else:
        asyncio.run(test_vision(sys.argv[1]))
