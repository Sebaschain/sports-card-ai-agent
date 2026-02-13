#!/bin/bash
# Manual Railway Login Script for Sports Card AI Agent

echo "🚀 SPORTS CARD AI AGENT - RAILWAY DEPLOYMENT"
echo "================================================="

# Get API token from user
echo "🔑 Por favor, pega tu token de Railway aquí abajo:"
echo ""
echo "Formato esperado: railway-token-xxxxxxxxxxxxxxxxxxxx"
echo "Tu token:"

# Read token
read -p "Tu Railway API token (railway-token-xxxxxxxxxxxxxxxxxxxx): " RAILWAY_TOKEN="

if [ -z "$RAILWAY_TOKEN" ]; then
    echo "❌ No se proporcionó un token. Por favor:"
    echo "1. Ve a: https://railway.app/account"
    echo "2. Busca 'Personal Access Tokens'"
    echo "3. Crear nuevo token con nombre 'sports-card-deployment'"
    echo "4. Copia el token y pégalo aquí"
    echo ""
    echo "5. Presiona Enter para continuar..."
    echo ""
    read -p "RAILWAY_TOKEN="
    
    if [ ! -z "$RAILWAY_TOKEN" ]; then
        echo "❌ No se proporcionó un token válido."
        echo "📋 Por favor, intenta de nuevo."
        echo "1. Ve a: https://railway.app/account"
        echo "2. Crea Personal Access Token: sports-card-deployment"
        echo "3. Crea el token y cópialo"
        echo "4. Vuelve y pega el token aquí."
        echo ""
        read -p "Presiona Enter para salir..."
    else
        echo "✅ Token recibido: ${RAILWAY_TOKEN:0:20}"
        echo ""
        echo "🔑 Insertando token en el script de deployment..."
        
        # Update the deployment script with actual token
        sed -i "s/railway variables set RAILWAY_TOKEN=.*/RAILWAY_TOKEN=.*/g" deploy-railway-final.sh > deploy-railway-with-token-temp.sh
        
        echo "✅ Token configurado exitosamente!"
        echo ""
        echo "📋 Siguiente paso:"
        echo "1. Ejecutar: ./deploy-railway-with-token-temp.sh"
        echo "2. Verificar deployment en: https://railway.app"
        echo "3. Una vez confirmado, copia las variables reales en .env.production"
        echo ""
        echo "🚀 La aplicación se desplegará en 5-10 minutos."
        echo "    Puedes verificar el progreso con: railway status"
        echo ""
        echo "🎉🏆 ¡PREPÁRATE PARA LANCAMIENTO! 🚀"
        
        exit 0
    fi
else
    echo "✅ Usando token proporcionado: ${RAILWAY_TOKEN:0:20}"
    
    # Execute deployment with token
    echo "🚀 Ejecutando deployment con el token configurado..."
    ./deploy-railway-final.sh
fi