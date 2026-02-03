# Guía de Configuración: Servidor MCP del Sports Card Agent

Esta guía te explica cómo conectar tu Agente de IA con otros clientes como **Claude Desktop**.

## 1. Instalación de Dependencias
Asegúrate de tener instalada la librería `mcp` en tu entorno virtual:
```powershell
pip install mcp
```

## 2. Configuración para Claude Desktop
Para que Claude pueda consultar tus tarjetas, añade lo siguiente a tu archivo `claude_desktop_config.json` (usualmente en `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sports-card-agent": {
      "command": "python.exe",
      "args": [
        "c:/Users/Sebastian/Documents/sports_cards/sports-card-ai-agent/src/mcp_server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "tu_clave_aqui",
        "DATABASE_URL": "sqlite:///c:/Users/Sebastian/Documents/sports_cards/sports-card-ai-agent/data/sports_cards.db"
      }
    }
  }
}
```
> [!NOTE]
> Asegúrate de usar la ruta completa a tu ejecutable de python si no está en el PATH.

## 3. Capacidades Disponibles
Una vez conectado, puedes preguntarle a Claude:
- "¿Qué tarjetas tengo en mi portfolio?" (Usa el recurso `portfolio://all`)
- "Busca en eBay el precio actual de LeBron James 2003 Topps" (Usa la herramienta `search_market`)
- "Analiza si es buen momento para comprar esta tarjeta..." (Usa la herramienta `analyze_card`)

## 4. Probar Localmente
Puedes verificar que el servidor inicia correctamente ejecutando:
```powershell
python src/mcp_server.py
```
El servidor esperará comandos vía `stdio`.
