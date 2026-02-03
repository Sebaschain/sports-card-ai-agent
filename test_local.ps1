# Script PowerShell para probar la app localmente sin Docker

Write-Host "🧪 Test Local - Sports Card AI Agent" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

# Verificar Python
Write-Host "1. Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "   ✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python no encontrado. Instala Python 3.11+" -ForegroundColor Red
    exit 1
}

# Verificar si existe venv
Write-Host "`n2. Verificando entorno virtual..." -ForegroundColor Yellow
if (!(Test-Path "venv")) {
    Write-Host "   ⚠️  Entorno virtual no existe. Creando..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "   ✅ Entorno virtual creado" -ForegroundColor Green
} else {
    Write-Host "   ✅ Entorno virtual existe" -ForegroundColor Green
}

# Activar venv
Write-Host "`n3. Activando entorno virtual..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "   ✅ Entorno virtual activado" -ForegroundColor Green

# Instalar dependencias
Write-Host "`n4. Instalando dependencias..." -ForegroundColor Yellow
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
Write-Host "   ✅ Dependencias instaladas" -ForegroundColor Green

# Verificar .env
Write-Host "`n5. Verificando archivo .env..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Write-Host "   ⚠️  Archivo .env no existe" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host "   ✅ Archivo .env creado desde .env.example" -ForegroundColor Green
        Write-Host "   ⚠️  IMPORTANTE: Edita .env con tus API keys antes de continuar" -ForegroundColor Yellow
    } else {
        Write-Host "   ❌ No existe .env.example. Crea .env manualmente." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ✅ Archivo .env existe" -ForegroundColor Green
}

# Crear directorio de datos
Write-Host "`n6. Creando directorios necesarios..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path data | Out-Null
New-Item -ItemType Directory -Force -Path logs | Out-Null
Write-Host "   ✅ Directorios creados" -ForegroundColor Green

# Inicializar base de datos
Write-Host "`n7. Inicializando base de datos..." -ForegroundColor Yellow
try {
    python init_database.py
    Write-Host "   ✅ Base de datos inicializada" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Error inicializando BD (puede que ya exista)" -ForegroundColor Yellow
}

# Resumen
Write-Host "`n====================================" -ForegroundColor Cyan
Write-Host "✅ Preparación completada!" -ForegroundColor Green
Write-Host "`nPara ejecutar la app:" -ForegroundColor Cyan
Write-Host "   streamlit run app.py" -ForegroundColor White
Write-Host "`nLuego abre: http://localhost:8501" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan
