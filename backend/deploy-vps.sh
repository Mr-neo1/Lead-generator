#!/bin/bash
# Lead Engine - VPS Deployment Script
# Requires: Ubuntu 22.04+ with Docker installed

set -e

echo "=== Lead Engine VPS Deployment ==="

# Check minimum RAM (2GB = 2097152 KB)
TOTAL_RAM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
if [ "$TOTAL_RAM" -lt 2000000 ]; then
    echo "WARNING: Less than 2GB RAM detected. Performance may be poor."
    echo "Recommended: 2GB minimum, 4GB for production"
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose plugin if not present
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
fi

# Create app directory
APP_DIR=/opt/leadengine
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy files (run this from the backend directory)
echo "Copying application files..."
cp -r . $APP_DIR/

cd $APP_DIR

# Use light config for small VPS
echo "Starting with lightweight configuration..."
docker compose -f docker-compose.light.yml up -d --build

echo ""
echo "=== Deployment Complete ==="
echo "API: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "Commands:"
echo "  View logs:    docker compose -f docker-compose.light.yml logs -f"
echo "  Stop:         docker compose -f docker-compose.light.yml down"
echo "  Restart:      docker compose -f docker-compose.light.yml restart"
echo ""
