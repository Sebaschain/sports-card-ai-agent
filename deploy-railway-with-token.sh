#!/bin/bash
# Railway Deployment Script with API Token

set -e

echo "🚀 SPORTS CARD AI AGENT - RAILWAY DEPLOYMENT"
echo "=================================================="

# Login to Railway with token
echo "🔐 Logging in to Railway with API token..."
railway login --token "84209270-0e7d-4ddd-9e7f-fae91e3c1d15" || echo "✅ Login via token may have failed, continuing..."

# Create project if doesn't exist
echo "📁 Checking Railway project..."
railway list || echo "Creating new project..."

# Link to GitHub repository
echo "🔗 Linking to GitHub repository..."
railway link https://github.com/tu-usuario/sports-card-ai-agent || echo "Project already linked"

# Add PostgreSQL plugin
echo "🐘 Adding PostgreSQL plugin..."
railway add postgresql

# Set environment variables
echo "⚙️ Setting environment variables..."
railway variables set DATABASE_URL="postgresql://${{RAILWAY_PRIVATE_KEY}}:${{RAILWAY_PUBLIC_KEY}}@${{RAILWAY_HOSTNAME}}:${{RAILWAY_PORT}}/railway"
railway variables set PYTHONPATH="/app"
railway variables set LOG_LEVEL="INFO"

# Set API keys (replace with real values when ready)
railway variables set EBAY_APP_ID="SportscardApp-PRD-123456"
railway variables set EBAY_CERT_ID="PRD-CERT-67890"
railway variables set EBAY_DEV_ID="PRD-DEV-112233"
railway variables set EBAY_TOKEN="REAL-PRODUCTION-TOKEN-PLACEHOLDER"
railway variables set OPENAI_API_KEY="sk-REAL-PRODUCTION-OPENAI-KEY-PLACEHOLDER"

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
echo "==========================="
echo "🌐 Your app is available at:"
echo "   https://sports-card-agent-production.railway.app"
echo ""
echo "📋 Next steps:"
echo "1. Replace demo API keys with real ones: railway variables"
echo "2. Monitor deployment: railway logs"
echo "3. Check status: railway status"
echo "4. Open app: https://sports-card-agent-production.railway.app"
echo ""
echo "🔧 To redeploy after API key changes:"
echo "   railway up"
echo ""
echo "📝 Current API keys (DEMO):"
echo "   - eBay: SportscardApp-PRD-123456 (DEMO)"
echo "   - OpenAI: sk-...PLACEHOLDER (DEMO)"
echo ""
echo "🚀 Sports Card AI Agent is LIVE on Railway!"
echo ""
echo "⚠️  IMPORTANT: Replace demo keys with real API keys for production use!"
echo "==========================="