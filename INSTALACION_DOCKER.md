# 🐳 Instalación de Docker en Windows

## Instalación Rápida

### Paso 1: Descargar Docker Desktop

1. Ve a: https://www.docker.com/products/docker-desktop/
2. Descarga **Docker Desktop for Windows**
3. Ejecuta el instalador `Docker Desktop Installer.exe`

### Paso 2: Instalar

1. ✅ Marca "Use WSL 2 instead of Hyper-V" (recomendado)
2. ✅ Acepta los términos
3. ✅ Instala
4. **Reinicia tu computadora** cuando se solicite

### Paso 3: Verificar Instalación

Después de reiniciar:

```powershell
# Abrir PowerShell y ejecutar:
docker --version
docker compose version

# Deberías ver algo como:
# Docker version 24.0.0
# Docker Compose version v2.20.0
```

### Paso 4: Iniciar Docker Desktop

1. Busca "Docker Desktop" en el menú de inicio
2. Ábrelo y espera a que inicie (icono de ballena en la bandeja del sistema)
3. Verifica que dice "Docker Desktop is running"

---

## ⚠️ Requisitos del Sistema

- Windows 10 64-bit: Pro, Enterprise, o Education (Build 19041 o superior)
- Windows 11 64-bit: Home o Pro versión 21H2 o superior
- Habilitar características de Windows:
  - Hyper-V
  - Containers
  - WSL 2 (Windows Subsystem for Linux)

**Docker Desktop configura esto automáticamente durante la instalación.**

---

## 🚀 Después de Instalar

Una vez instalado, puedes ejecutar:

```powershell
cd c:\Users\Sebastian\Documents\sports_cards\sports-card-ai-agent

# Verificar que funciona
docker-compose --version

# Construir la imagen
docker-compose build

# Iniciar la aplicación
docker-compose up
```

---

## ❓ Problemas Comunes

### "Docker Desktop no inicia"
- Verifica que WSL 2 esté instalado: `wsl --status`
- Si no está: `wsl --install`

### "Error de permisos"
- Ejecuta PowerShell como Administrador
- O verifica que Docker Desktop esté corriendo

### "Puerto ya en uso"
- Cierra otras aplicaciones usando puerto 8501
- O cambia el puerto en `docker-compose.yml`

---

## 📚 Recursos

- Documentación oficial: https://docs.docker.com/desktop/install/windows-install/
- Guía de WSL 2: https://docs.microsoft.com/en-us/windows/wsl/install
