#!/bin/bash
# Lead Engine - Update Deployment Script
# Run this on your VPS after pushing changes to GitHub

set -e

APP_DIR=/opt/leadengine
COMPOSE_FILE="docker-compose.light.yml"

echo "=== Lead Engine Update Deployment ==="

cd $APP_DIR

# Pull latest code
echo "1. Pulling latest changes..."
git pull origin main

# Run database migrations
echo "2. Running database migrations..."
docker compose -f $COMPOSE_FILE exec -T api python migrate.py

# Rebuild and restart containers
echo "3. Rebuilding containers..."
docker compose -f $COMPOSE_FILE build --no-cache api worker

echo "4. Restarting services..."
docker compose -f $COMPOSE_FILE up -d api worker

# Show status
echo ""
echo "=== Update Complete ==="
docker compose -f $COMPOSE_FILE ps

echo ""
echo "View logs: docker compose -f $COMPOSE_FILE logs -f api worker"
