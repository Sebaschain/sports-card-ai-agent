#!/bin/bash
# Deploy to Streamlit Cloud
# Usage: ./deploy.sh

set -e

echo "=== Sports Card AI - Deployment Script ==="

# Verificar que estamos en main
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "Error: Deploy solo desde main branch"
    exit 1
)

# Verificar cambios
if [ -z "$(git status --porcelain)" ]; then
    echo "No hay cambios para deploy"
    exit 0
fi

echo "1. Ejecutando tests..."
python -m pytest tests/unit/ -v --tb=short || echo "Warning: Tests failed"

echo "2. Sync dependencies..."
uv sync

echo "3. Commit changes..."
git add .
git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M')"

echo "4. Push to remote..."
git push origin main

echo ""
echo "=== Streamlit Cloud detectará el push automáticamente ==="
echo "Verifica en: https://share.streamlit.io/"
