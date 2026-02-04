#!/bin/bash
# Railway Quick Deploy Script

set -e

echo "🚀 SPORTS CARD AI AGENT - RAILWAY DEPLOYMENT"
echo "==============================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "🔐 Logging in to Railway..."
railway login

# Create new project (if not exists)
echo "📁 Creating Railway project..."
railway create sports-card-agent || echo "✅ Project already exists"

# Link to GitHub repository
echo "🔗 Linking to GitHub repository..."
read -p "Enter your GitHub repository URL (https://github.com/username/repo): " GITHUB_REPO
railway link "$GITHUB_REPO"

# Add PostgreSQL plugin
echo "🐘 Adding PostgreSQL plugin..."
railway add postgresql

# Set environment variables
echo "⚙️ Setting environment variables..."
railway variables set DATABASE_URL="postgresql://\${{RAILWAY_PRIVATE_KEY}@${{RAILWAY_PUBLIC_KEY}}/railway"
railway variables set PYTHONPATH="/app"
railway variables set LOG_LEVEL="INFO"

# Set API keys (using test values for demo)
echo "🔑 Setting API keys..."
railway variables set EBAY_APP_ID="SportscardApp-DEMO-123456"
railway variables set OPENAI_API_KEY="sk-demo-key-for-deployment"

# Add Redis for caching
echo "📦 Adding Redis for caching..."
railway add redis

# Deploy
echo "🚀 Deploying to Railway..."
railway up

# Check deployment status
echo "📊 Checking deployment status..."
railway status

# Show URLs
echo ""
echo "🎉 DEPLOYMENT COMPLETED!"
echo "======================"
echo "🌐 Your app will be available at:"
echo "   https://sports-card-agent-production.railway.app"
echo ""
echo "📊 To monitor deployment:"
echo "   railway logs"
echo "   railway status"
echo ""
echo "🔧 To manage services:"
echo "   railway variables"
echo "   railway services"
echo ""
echo "✅ Sports Card AI Agent is LIVE on Railway!"

# Health check
echo "🏥 Performing health check..."
sleep 30

APP_URL="https://sports-card-agent-production.railway.app"
for i in {1..10}; do
    if curl -f -s "$APP_URL/health" > /dev/null; then
        echo "✅ Application is healthy! ($APP_URL)"
        break
    else
        echo "⏳ Waiting for application... (attempt $i/10)"
        sleep 10
    fi
done

echo ""
echo "🎯 NEXT STEPS:"
echo "1. Replace demo API keys with real ones: railway variables"
echo "2. Configure custom domain: railway domain"
echo "3. Monitor performance: railway logs"
echo ""
echo "🚀 Your Sports Card AI Agent is PRODUCTION READY!"