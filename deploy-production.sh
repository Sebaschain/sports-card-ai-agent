#!/bin/bash
# Complete Production Deployment Script

set -e

echo "🚀 SPORTS CARD AI AGENT - PRODUCTION DEPLOYMENT"
echo "=================================================="

# Step 1: Build Docker Image
echo "📦 Building production Docker image..."
docker build -f Dockerfile.production -t sports-card-agent:latest .

# Step 2: Tag and Push (to registry)
if [ "$1" == "push" ]; then
    echo "📤 Pushing Docker image to registry..."
    docker tag sports-card-agent:latest your-registry/sports-card-agent:latest
    docker push your-registry/sports-card-agent:latest
fi

# Step 3: Deploy Production Services
echo "🚀 Deploying to production..."
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d

# Step 4: Wait for Services
echo "⏳ Waiting for services to be ready..."
sleep 30

# Step 5: Run Database Migrations
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.production.yml exec app python scripts/migrate-production-db.sh

# Step 6: Health Check
echo "🏥 Performing health check..."
sleep 10

# Check if services are running
if docker-compose -f docker-compose.production.yml ps | grep -q "Up"; then
    echo "✅ All services are running!"
else
    echo "❌ Some services failed to start!"
    docker-compose -f docker-compose.production.yml logs
    exit 1
fi

# Step 7: Verify Application
echo "🌐 Verifying application health..."
for i in {1..10}; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Application is healthy!"
        break
    else
        echo "⏳ Waiting for application... (attempt $i/10)"
        sleep 10
    fi
done

# Step 8: Show URLs
echo ""
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "=================="
echo "🌐 Local URLs:"
echo "   HTTP: http://localhost:80"
echo "   HTTPS: https://localhost:443"
echo "   App (direct): http://localhost:8501"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.production.yml ps
echo ""
echo "📝 To view logs: docker-compose -f docker-compose.production.yml logs -f"
echo ""
echo "🔧 To stop: docker-compose -f docker-compose.production.yml down"
echo ""

# If this is a Railway deployment
if [ "$2" == "railway" ]; then
    echo "🚂 Railway Deployment:"
    echo "   Status: railway status"
    echo "   Logs: railway logs"
    echo "   Variables: railway variables"
    echo "   Domain: railway domain"
fi

echo "🎯 Sports Card AI Agent is now LIVE!"