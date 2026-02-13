#!/bin/bash
# Railway Deployment Script - Final Corrected Version

set -e

echo "🚀 SPORTS CARD AI AGENT - RAILWAY DEPLOYMENT"
echo "==================================================="

# Check for browser login option
if [ "$1" == "--browser" ]; then
    echo "🌐 Abriendo login en navegador para Railway..."
    railway login
    echo "✅ Por favor completa el login en el navegador que se abrirá"
    echo "Una vez completado, vuelve a esta terminal y ejecuta:"
    echo "  ./deploy-railway-final.sh"
    exit 0
fi

# Set Railway authentication token (production ready)
echo "🔐 Usando sesión local de Railway..."
# railway variables set RAILWAY_TOKEN="84209270-0e7d-4ddd-9e7f-fae91e3c1d15"

# Check if project exists
echo "📁 Verificando Railway project..."
railway list > /dev/null 2>&1

# Link to GitHub repository  
echo "🔗 Conectando a GitHub repository..."
railway link https://github.com/Sebaschain/sports-card-ai-agent 2>/dev/null || echo "✅ Proyecto ya conectado"

# Add PostgreSQL plugin
echo "🐘 Agregando PostgreSQL plugin..."
railway add postgresql 2>/dev/null || echo "✅ PostgreSQL ya configurado"

# Set environment variables
echo "⚙️ Configurando variables de entorno..."
railway variables set DATABASE_URL="postgresql://${{RAILWAY_PRIVATE_KEY}}:${{RAILWAY_PUBLIC_KEY}}@${{RAILWAY_HOSTNAME}}:${{RAILWAY_PORT}}/railway"
railway variables set PYTHONPATH="/app"
railway variables set LOG_LEVEL="INFO"

# Set API keys (demo for now)
railway variables set EBAY_APP_ID="SportscardApp-DEMO-123456"
railway variables set EBAY_CERT_ID="DEMO-CERT-67890"
railway variables set EBAY_DEV_ID="DEMO-DEV-112233"
railway variables set EBAY_TOKEN="DEMO-TOKEN-PLACEHOLDER"
railway variables set OPENAI_API_KEY="sk-demo-key-for-deployment"

# Deploy
echo "🚀 Desplegando a Railway..."
railway up

# Wait for deployment
echo "⏳ Esperando que el deployment esté listo..."
sleep 45

# Check deployment status
echo "📊 Verificando estado del deployment..."
railway status

# Wait a bit more
sleep 15

# Check if services are running
echo "🔍 Verificando servicios..."
railway status

echo ""
echo "🎉 DESPLOYMENT COMPLETED!"
echo "=========================="
echo "🌐 Tu app está disponible en:"
echo "   https://sports-card-agent-production.railway.app"
echo ""
echo "📋 Pasos siguientes:"
echo "1. Reemplazar claves API demo con claves reales: railway variables"
echo "2. Monitoriar deployment: railway logs"
echo "3. Verificar status: railway status"
echo "4. Abrir aplicación: https://sports-card-agent-production.railway.app"
echo ""
echo "🔧 Para actualizar variables:"
echo "   railway variables set EBAY_APP_ID=TU_CLAVE_REAL"
echo "   railway variables set OPENAI_API_KEY=TU_CLAVE_OPENAI"
echo ""
echo "🔧 Para redeployar:"
echo "   railway up"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   Las variables actuales son DEMO"
echo "   Reemplazarlas con claves reales para producción"
echo "=========================="
echo ""
echo "🚀 Sports Card AI Agent está LIVE!"
echo ""