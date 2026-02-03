import base64
import json
import httpx
from typing import Dict, Any, Optional
from src.utils.config import settings
from src.tools.base_tool import BaseTool


class CardVisionTool(BaseTool):
    """Herramienta para identificar tarjetas deportivas mediante Vision AI (GPT-4o)"""

    def __init__(self):
        self._name = "Card Vision Tool"
        self.api_key = settings.OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/chat/completions"

    @property
    def tool_name(self) -> str:
        return self._name

    def _encode_image(self, image_content: bytes) -> str:
        """Codifica la imagen en base64"""
        return base64.b64encode(image_content).decode("utf-8")

    async def identify_card(self, image_content: bytes) -> Dict[str, Any]:
        """
        Analiza la imagen de una tarjeta y extrae sus metadatos
        """
        if not self.api_key:
            return {"success": False, "error": "OpenAI API Key no configurada"}

        base64_image = self._encode_image(image_content)

        prompt = """
        Eres un experto en coleccionismo de tarjetas deportivas (NBA, MLB, NHL).
        Analiza esta imagen y extrae la información de la tarjeta.
        Responde ÚNICAMENTE en formato JSON con la siguiente estructura:
        {
            "player_name": "Nombre completo",
            "year": 2023 (número),
            "manufacturer": "Ej: Topps, Panini, Upper Deck",
            "set_name": "Ej: Prizm, Chrome, Series 1",
            "card_number": "Número de tarjeta",
            "variant": "Ej: Rookie Card, Refractor, Base",
            "is_graded": true/false,
            "grading_company": "Ej: PSA, BGS, SGC",
            "grade": 9.5 (número o null),
            "sport": "NBA/MLB/NHL",
            "confidence": 0.0 a 1.0 (número)
        }
        Si no estás seguro de algún campo, pon null o "Unknown".
        """

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 500,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url, headers=headers, json=payload
                )
                response.raise_for_status()
                result = response.json()

                content = result["choices"][0]["message"]["content"]
                card_data = json.loads(content)
                card_data["success"] = True
                return card_data

        except Exception as e:
            return {"success": False, "error": str(e)}
