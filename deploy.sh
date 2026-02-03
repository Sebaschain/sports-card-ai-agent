#!/bin/bash
# Script de despliegue para producción

set -e  # Salir si hay errores

echo "🚀 Iniciando despliegue..."

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que .env existe
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: Archivo .env no encontrado${NC}"
    echo "Crea un archivo .env con las variables necesarias"
    exit 1
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker no está instalado${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Error: Docker Compose no está instalado${NC}"
    exit 1
fi

# Construir imágenes
echo -e "${YELLOW}📦 Construyendo imágenes Docker...${NC}"
docker-compose build

# Detener contenedores existentes
echo -e "${YELLOW}🛑 Deteniendo contenedores existentes...${NC}"
docker-compose down

# Iniciar servicios
echo -e "${YELLOW}▶️  Iniciando servicios...${NC}"
docker-compose up -d

# Esperar a que los servicios estén listos
echo -e "${YELLOW}⏳ Esperando a que los servicios estén listos...${NC}"
sleep 10

# Verificar salud de los servicios
echo -e "${YELLOW}🏥 Verificando salud de los servicios...${NC}"
docker-compose ps

# Inicializar base de datos
echo -e "${YELLOW}🗄️  Inicializando base de datos...${NC}"
docker-compose exec -T app python init_database.py || echo "Base de datos ya inicializada"

# Ver logs
echo -e "${GREEN}✅ Despliegue completado!${NC}"
echo -e "${YELLOW}📋 Ver logs con: docker-compose logs -f${NC}"
echo -e "${YELLOW}🌐 Aplicación disponible en: http://localhost:8501${NC}"
