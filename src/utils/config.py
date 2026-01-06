
"""
Configuración del proyecto
Carga variables de entorno y configuraciones globales
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Directorios del proyecto
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

# Crear directorios si no existen
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Settings:
    """Configuración global de la aplicación"""
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # eBay API
    EBAY_APP_ID: str = os.getenv("EBAY_APP_ID", "")
    EBAY_CERT_ID: str = os.getenv("EBAY_CERT_ID", "")
    EBAY_DEV_ID: str = os.getenv("EBAY_DEV_ID", "")
    EBAY_TOKEN: str = os.getenv("EBAY_TOKEN", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/sports_cards.db")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Project
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Sports Card AI Agent")
    VERSION: str = os.getenv("VERSION", "0.1.0")


# Instancia global de configuración
settings = Settings()