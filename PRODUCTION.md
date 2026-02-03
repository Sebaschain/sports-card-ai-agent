# 🚀 Guía de Despliegue a Producción

Esta guía te ayudará a llevar tu Sports Card AI Agent a producción de forma segura y escalable.

## 📋 Tabla de Contenidos

1. [Preparación](#preparación)
2. [Configuración](#configuración)
3. [Despliegue con Docker](#despliegue-con-docker)
4. [Despliegue en la Nube](#despliegue-en-la-nube)
5. [Seguridad](#seguridad)
6. [Monitoreo y Logging](#monitoreo-y-logging)
7. [Backup y Recuperación](#backup-y-recuperación)
8. [Escalabilidad](#escalabilidad)

---

## 🔧 Preparación

### 1. Revisar Dependencias

```bash
# Verificar que todas las dependencias estén en requirements.txt
pip freeze > requirements_check.txt
```

### 2. Limpiar Código

- ✅ Eliminar código de debug
- ✅ Remover prints innecesarios
- ✅ Verificar manejo de errores
- ✅ Revisar imports no utilizados

### 3. Testing

```bash
# Ejecutar tests
python -m pytest tests/

# Verificar que no hay errores de importación
python -c "from src.agents import *; print('OK')"
```

---

## ⚙️ Configuración

### Variables de Entorno

Crea un archivo `.env.production` (NO subirlo a Git):

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# eBay API
EBAY_APP_ID=...
EBAY_CERT_ID=...
EBAY_DEV_ID=...
EBAY_TOKEN=...

# Database (PostgreSQL en producción)
DATABASE_URL=postgresql://user:password@host:5432/sports_cards

# Logging
LOG_LEVEL=INFO

# Seguridad
SECRET_KEY=generar_clave_segura_aqui
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
```

### Base de Datos

**Opción 1: PostgreSQL (Recomendado para producción)**

```bash
# Instalar PostgreSQL
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Crear base de datos
sudo -u postgres psql
CREATE DATABASE sports_cards;
CREATE USER sports_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE sports_cards TO sports_user;
\q

# Actualizar DATABASE_URL
DATABASE_URL=postgresql://sports_user:secure_password@localhost:5432/sports_cards
```

**Opción 2: SQLite (Solo para desarrollo/testing)**

```bash
# SQLite es suficiente para desarrollo, pero NO para producción
DATABASE_URL=sqlite:///./data/sports_cards.db
```

### Configurar Logging

Crea `src/utils/logging_config.py`:

```python
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logging(log_level: str = "INFO"):
    """Configurar logging para producción"""
    
    # Crear directorio de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Formato de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para archivo (con rotación)
    file_handler = RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger
```

---

## 🐳 Despliegue con Docker

### 1. Construir Imagen

```bash
docker build -t sports-card-ai-agent:latest .
```

### 2. Ejecutar con Docker Compose

```bash
# Copiar .env.production a .env (o usar docker secrets)
cp .env.production .env

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f app

# Verificar estado
docker-compose ps
```

### 3. Inicializar Base de Datos

```bash
# Ejecutar migraciones
docker-compose exec app python init_database.py
```

---

## ☁️ Despliegue en la Nube

### Opción 1: AWS (EC2 + RDS)

**1. Crear instancia EC2**

```bash
# Conectarse a EC2
ssh -i key.pem ubuntu@ec2-instance

# Instalar Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo usermod -aG docker ubuntu

# Clonar repositorio
git clone https://github.com/tu-usuario/sports-card-ai-agent.git
cd sports-card-ai-agent
```

**2. Configurar RDS (PostgreSQL)**

- Crear instancia RDS PostgreSQL
- Obtener endpoint: `your-db.region.rds.amazonaws.com`
- Actualizar `DATABASE_URL` en `.env`

**3. Desplegar**

```bash
# Configurar variables de entorno
nano .env

# Iniciar servicios
docker-compose up -d

# Configurar Nginx (reverse proxy)
sudo apt-get install nginx
sudo nano /etc/nginx/sites-available/sports-cards
```

**Nginx config:**

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**4. SSL con Let's Encrypt**

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

### Opción 2: Heroku

```bash
# Instalar Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Crear app
heroku create sports-card-ai-agent

# Configurar variables
heroku config:set OPENAI_API_KEY=sk-...
heroku config:set DATABASE_URL=postgresql://...

# Agregar PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Desplegar
git push heroku main

# Ver logs
heroku logs --tail
```

### Opción 3: Railway

1. Conectar repositorio en Railway
2. Configurar variables de entorno
3. Railway detecta automáticamente Dockerfile
4. Despliegue automático en cada push

### Opción 4: DigitalOcean App Platform

1. Conectar repositorio
2. Seleccionar Dockerfile
3. Configurar variables de entorno
4. Desplegar

---

## 🔒 Seguridad

### 1. Secrets Management

**NO subir `.env` a Git**

```bash
# .gitignore ya incluye .env
# Usar servicios de secrets:
# - AWS Secrets Manager
# - HashiCorp Vault
# - Docker Secrets
# - Kubernetes Secrets
```

### 2. Rate Limiting

Agregar rate limiting para APIs:

```python
# src/utils/rate_limiter.py
from functools import wraps
import time
from collections import defaultdict

rate_limits = defaultdict(list)

def rate_limit(max_calls=10, period=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            key = f"{func.__name__}"
            
            # Limpiar llamadas antiguas
            rate_limits[key] = [
                call_time for call_time in rate_limits[key]
                if now - call_time < period
            ]
            
            # Verificar límite
            if len(rate_limits[key]) >= max_calls:
                raise Exception(f"Rate limit exceeded: {max_calls} calls per {period}s")
            
            rate_limits[key].append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### 3. Validación de Input

```python
# Validar todos los inputs del usuario
from pydantic import BaseModel, validator

class PlayerSearchRequest(BaseModel):
    player_name: str
    sport: str
    
    @validator('player_name')
    def validate_name(cls, v):
        if len(v) < 2 or len(v) > 100:
            raise ValueError('Invalid player name length')
        return v.strip()
```

### 4. HTTPS

- ✅ Usar HTTPS en producción
- ✅ Configurar certificados SSL (Let's Encrypt)
- ✅ Forzar redirección HTTP → HTTPS

---

## 📊 Monitoreo y Logging

### 1. Logging Estructurado

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log(self, level, message, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        getattr(self.logger, level.lower())(json.dumps(log_entry))
```

### 2. Health Checks

```python
# health_check.py
from fastapi import FastAPI
from src.utils.database import engine
from sqlalchemy import text

app = FastAPI()

@app.get("/health")
async def health_check():
    try:
        # Verificar base de datos
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }, 503
```

### 3. Métricas

- **Uptime**: UptimeRobot, Pingdom
- **APM**: New Relic, Datadog, Sentry
- **Logs**: Loggly, Papertrail, CloudWatch

---

## 💾 Backup y Recuperación

### 1. Backup de Base de Datos

```bash
# Script de backup diario
#!/bin/bash
# backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="sports_cards"

# Backup PostgreSQL
pg_dump $DATABASE_URL > $BACKUP_DIR/backup_$DATE.sql

# Comprimir
gzip $BACKUP_DIR/backup_$DATE.sql

# Eliminar backups antiguos (mantener 30 días)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Subir a S3 (opcional)
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://tu-bucket/backups/
```

### 2. Restaurar Backup

```bash
# Restaurar desde backup
gunzip backup_20240101_120000.sql.gz
psql $DATABASE_URL < backup_20240101_120000.sql
```

### 3. Cron Job

```bash
# Agregar a crontab
crontab -e

# Backup diario a las 2 AM
0 2 * * * /path/to/backup_db.sh
```

---

## 📈 Escalabilidad

### 1. Caching

```python
# Usar Redis para cache
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(ttl=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Intentar obtener de cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Ejecutar función
            result = func(*args, **kwargs)
            
            # Guardar en cache
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator
```

### 2. Load Balancing

```nginx
# nginx.conf
upstream streamlit_backend {
    least_conn;
    server app1:8501;
    server app2:8501;
    server app3:8501;
}

server {
    location / {
        proxy_pass http://streamlit_backend;
    }
}
```

### 3. Queue System (Celery)

Para tareas asíncronas pesadas:

```python
# tasks.py
from celery import Celery

celery_app = Celery('sports_cards')

@celery_app.task
def analyze_card_async(player_name, year):
    # Análisis pesado en background
    pass
```

---

## ✅ Checklist de Producción

- [ ] Variables de entorno configuradas
- [ ] Base de datos PostgreSQL configurada
- [ ] Logging configurado
- [ ] HTTPS/SSL configurado
- [ ] Secrets no en Git
- [ ] Health checks implementados
- [ ] Backups configurados
- [ ] Monitoreo configurado
- [ ] Rate limiting implementado
- [ ] Tests pasando
- [ ] Documentación actualizada
- [ ] Plan de rollback preparado

---

## 🆘 Troubleshooting

### Problemas Comunes

**1. Error de conexión a base de datos**
```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Verificar conexión
psql $DATABASE_URL
```

**2. Puerto ya en uso**
```bash
# Encontrar proceso usando puerto 8501
lsof -i :8501
kill -9 <PID>
```

**3. Out of memory**
```bash
# Aumentar límite de memoria en Docker
docker-compose.yml:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
```

---

## 📞 Soporte

Para más ayuda:
- 📧 Email: soporte@tu-dominio.com
- 📚 Documentación: https://docs.tu-dominio.com
- 🐛 Issues: https://github.com/tu-usuario/sports-card-ai-agent/issues
