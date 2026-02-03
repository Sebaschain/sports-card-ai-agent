import httpx
import asyncio
import json


async def test_ebay_fix():
    app_id = "Sbastien-sportcar-PRD-a113ecf9c-738789f3"
    base_url = "https://svcs.ebay.com/services/search/FindingService/v1"

    # Intento 1: Con GLOBAL-ID y sin REST-PAYLOAD
    params = {
        "OPERATION-NAME": "findItemsAdvanced",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": app_id,
        "RESPONSE-DATA-FORMAT": "JSON",
        "GLOBAL-ID": "EBAY-US",
        "keywords": "LeBron James rookie card 2003",
        "paginationInput.entriesPerPage": "5",
        "sortOrder": "BestMatch",
    }

    print(f"--- Probando con GLOBAL-ID (EBAY-US) ---")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(base_url, params=params)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("✅ Éxito!")
                # print(response.text[:500])
            else:
                print(f"❌ Falló con status {response.status_code}")
                print(f"Respuesta: {response.text[:500]}")
        except Exception as e:
            print(f"❌ Error: {e}")

    # Intento 2: Usando findItemsByKeywords (más simple)
    params["OPERATION-NAME"] = "findItemsByKeywords"
    print(f"\n--- Probando con findItemsByKeywords ---")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(base_url, params=params)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("✅ Éxito con findItemsByKeywords!")
            else:
                print(f"❌ Falló con status {response.status_code}")
                print(f"Respuesta: {response.text[:500]}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_ebay_fix())
