# ⚡ Inicio Rápido - Producción

## 🚀 Despliegue Rápido (5 minutos)

### 1. Preparar Variables de Entorno

```bash
# Copiar ejemplo y editar
cp .env.example .env
nano .env  # Editar con tus API keys
```

### 2. Desplegar con Docker

```bash
# Opción A: Script automático (Linux/Mac)
chmod +x deploy.sh
./deploy.sh

# Opción B: Manual
docker-compose up -d
```

### 3. Verificar

```bash
# Ver logs
docker-compose logs -f

# Verificar que está corriendo
docker-compose ps

# Acceder a la aplicación
# http://localhost:8501
```

## 📋 Checklist Mínimo

- [ ] Variables de entorno configuradas (`.env`)
- [ ] Docker y Docker Compose instalados
- [ ] Puerto 8501 disponible
- [ ] Base de datos configurada (SQLite por defecto, PostgreSQL recomendado)

## 🔧 Configuración Básica

### Variables Mínimas Requeridas

```bash
# .env
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///./data/sports_cards.db  # O PostgreSQL
LOG_LEVEL=INFO
```

### Para Producción Real

1. **Cambiar a PostgreSQL:**
   ```bash
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ```

2. **Agregar HTTPS:**
   - Configurar dominio
   - Obtener certificado SSL (Let's Encrypt)
   - Descomentar sección HTTPS en `nginx.conf`

3. **Configurar Backups:**
   - Ver sección "Backup y Recuperación" en `PRODUCTION.md`

## 📚 Documentación Completa

Para más detalles, ver `PRODUCTION.md`:
- Despliegue en la nube (AWS, Heroku, Railway)
- Seguridad avanzada
- Monitoreo y logging
- Escalabilidad
- Troubleshooting

## 🆘 Problemas Comunes

**Puerto en uso:**
```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8502:8501"  # Usar 8502 en lugar de 8501
```

**Error de base de datos:**
```bash
# Inicializar manualmente
docker-compose exec app python init_database.py
```

**Ver logs:**
```bash
docker-compose logs -f app
```
