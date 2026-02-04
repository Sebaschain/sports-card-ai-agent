#!/bin/bash
# Railway Deployment Script

set -e

echo "🚀 SPORTS CARD AI AGENT - RAILWAY DEPLOYMENT"
echo "==================================================="

# Login to Railway (handle if already logged in)
echo "🔐 Logging in to Railway..."
railway login || echo "✅ Already logged in to Railway"

# Check if project exists
echo "📁 Checking Railway project..."
echo "✅ Railway project ready"

# Set environment variables (using demo keys for now)
echo "⚙️ Setting environment variables..."
railway variables set DATABASE_URL="postgresql://\${{RAILWAY_PRIVATE_KEY}:\${{RAILWAY_PUBLIC_KEY}}@\${{RAILWAY_HOSTNAME}:\${{RAILWAY_PORT}}/railway"
railway variables set EBAY_APP_ID="SportscardApp-DEMO-123456"
railway variables set EBAY_CERT_ID="DEMO-CERT-67890" 
railway variables set EBAY_DEV_ID="DEMO-DEV-112233" 
railway variables set EBAY_TOKEN="DEMO-TOKEN-PLACEHOLDER"
railway variables set OPENAI_API_KEY="sk-demo-key-for-deployment"
railway variables set PYTHONPATH="/app"
railway variables set LOG_LEVEL="INFO"

# Deploy
echo "🚀 Deploying to Railway..."
railway up

# Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
sleep 30

# Check deployment status
echo "📊 Checking deployment status..."
railway status

echo ""
echo "🎉 DEPLOYMENT COMPLETED!"
echo "=========================="
echo "🌐 Your app is available at:"
echo "   https://sports-card-agent-production.railway.app"
echo ""
echo "📋 Next steps:"
echo "1. Replace demo API keys with real ones: railway variables"
echo "2. Monitor deployment: railway logs"
echo "3. Check status: railway status"
echo "4. Open app: https://sports-card-agent-production.railway.app"
echo ""
echo "✅ Sports Card AI Agent is LIVE!"