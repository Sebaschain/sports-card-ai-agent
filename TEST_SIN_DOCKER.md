# 🧪 Probar la App SIN Docker (Mientras Instalas Docker)

Si prefieres probar la aplicación directamente sin Docker primero, aquí está cómo:

## ✅ Requisitos Previos

1. Python 3.11+ instalado
2. Variables de entorno configuradas (`.env`)

## 🚀 Pasos para Probar

### Paso 1: Crear Entorno Virtual

```powershell
# En PowerShell
cd c:\Users\Sebastian\Documents\sports_cards\sports-card-ai-agent

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Si tienes error de ejecución de scripts:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Paso 2: Instalar Dependencias

```powershell
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 3: Configurar Variables de Entorno

```powershell
# Crear .env si no existe
if (!(Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Archivo .env creado. Edítalo con tus API keys."
}

# Editar .env con tus credenciales
notepad .env
```

**Variables mínimas necesarias:**
```bash
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///./data/sports_cards.db
LOG_LEVEL=INFO
```

### Paso 4: Inicializar Base de Datos

```powershell
# Crear directorio de datos
New-Item -ItemType Directory -Force -Path data

# Inicializar base de datos
python init_database.py
```

### Paso 5: Ejecutar la Aplicación

```powershell
# Ejecutar Streamlit
streamlit run app.py

# O con puerto específico
streamlit run app.py --server.port 8501
```

### Paso 6: Acceder a la App

Abre tu navegador en: **http://localhost:8501**

---

## ✅ Verificar que Funciona

1. ✅ La app carga en el navegador
2. ✅ Puedes hacer una búsqueda en eBay
3. ✅ El análisis de jugador funciona
4. ✅ No hay errores en la consola

---

## 🔄 Después de Probar

Una vez que verifiques que todo funciona:

1. **Instala Docker Desktop** (ver `INSTALACION_DOCKER.md`)
2. **Prueba con Docker** para simular producción
3. **Despliega a producción** cuando estés listo

---

## ⚠️ Notas Importantes

- **SQLite está bien para testing local**, pero usa PostgreSQL en producción
- **No uses esto en producción** - es solo para desarrollo/testing
- **Docker es necesario** para desplegar a producción correctamente

---

## 🐛 Si Hay Errores

### Error: "No module named X"
```powershell
pip install X
```

### Error: "Port already in use"
```powershell
# Cambiar puerto
streamlit run app.py --server.port 8502
```

### Error: "Database locked"
- Cierra otras instancias de la app
- O cambia a PostgreSQL

---

## 📝 Próximos Pasos

Después de verificar que funciona sin Docker:

1. ✅ Instala Docker Desktop
2. ✅ Prueba con `docker-compose up`
3. ✅ Sigue el `ROADMAP_PRODUCCION.md`
