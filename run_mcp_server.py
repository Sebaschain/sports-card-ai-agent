"""
Script para iniciar el servidor MCP
IMPORTANTE: No imprimir nada a stdout, solo comunicación MCP
"""
import asyncio
import sys
import os

# Redirigir prints a stderr para no interferir con MCP
class StderrLogger:
    def write(self, message):
        if message.strip():
            sys.stderr.write(message)
            sys.stderr.flush()
    
    def flush(self):
        sys.stderr.flush()

# Solo para debugging, comentar en producción
# sys.stdout = StderrLogger()

from src.mcp.server import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)