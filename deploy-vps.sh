#!/bin/bash
set -e

# VPS Deployment Script for Lead Engine
# Usage: ./deploy-vps.sh
# 
# REQUIRED environment variables:
#   VPS_IP - IP address of the VPS
#   VPS_USER - SSH user (default: root)
#   PROD_PASSWORD - Admin login password
#   PROD_SECRET - Session secret (min 32 chars)
#   API_KEY - Backend API key (min 32 chars)

VPS_IP="${VPS_IP:?Error: VPS_IP environment variable not set}"
VPS_USER="${VPS_USER:-root}"
PROD_PASSWORD="${PROD_PASSWORD:?Error: PROD_PASSWORD not set}"
PROD_SECRET="${PROD_SECRET:?Error: PROD_SECRET not set}"
API_KEY="${API_KEY:?Error: API_KEY not set}"

# Validate secret length
if [ ${#PROD_SECRET} -lt 32 ]; then
  echo "❌ Error: PROD_SECRET must be at least 32 characters"
  exit 1
fi

if [ ${#API_KEY} -lt 32 ]; then
  echo "❌ Error: API_KEY must be at least 32 characters"
  exit 1
fi

PROJECT_DIR="/root/Lead-generator"
STANDALONE_DIR="$PROJECT_DIR/.next/standalone"

echo "🚀 Starting VPS Deployment..."

# Step 1: Pull latest code from GitHub
echo "📥 Pulling latest code from GitHub..."
ssh "$VPS_USER@$VPS_IP" "cd $PROJECT_DIR && git pull origin main"

# Step 2: Build the frontend
echo "🔨 Building Next.js frontend..."
ssh "$VPS_USER@$VPS_IP" "cd $PROJECT_DIR && npm run build"

# Step 3: Remove old standalone build
echo "🧹 Cleaning old build files..."
ssh "$VPS_USER@$VPS_IP" "rm -rf $STANDALONE_DIR/.next $STANDALONE_DIR/public"

# Step 4: Copy new build to standalone
echo "📦 Copying new build to standalone directory..."
ssh "$VPS_USER@$VPS_IP" "cp -r $PROJECT_DIR/.next/static $STANDALONE_DIR/.next/static && cp -r $PROJECT_DIR/public $STANDALONE_DIR/public 2>/dev/null || true"

# Step 5: Ensure .env file exists in standalone
echo "⚙️  Ensuring environment variables are configured..."
ssh "$VPS_USER@$VPS_IP" "cat > $STANDALONE_DIR/.env << 'ENVEOF'
NEXT_PUBLIC_API_URL=https://leadscraper.freelanceleadsapp.tech
APP_URL=https://leadscraper.freelanceleadsapp.tech
APP_LOGIN_USERNAME=admin
APP_LOGIN_PASSWORD=\"${PROD_PASSWORD}\"
APP_LOGIN_SECRET=\"${PROD_SECRET}\"
ENVEOF"

# Step 5b: Set backend API key environment variable
echo "🔐 Configuring backend API key..."
ssh "$VPS_USER@$VPS_IP" "cat > /root/Lead-generator/.env.production << 'ENVEOF'
API_KEY=\"${API_KEY}\"
ENVEOF
export $(cat /root/Lead-generator/.env.production | xargs)"

# Step 6: Restart PM2
echo "🔄 Restarting application..."
ssh "$VPS_USER@$VPS_IP" "pm2 restart frontend && sleep 3"

# Step 7: Verify deployment
echo "✅ Verifying deployment..."
ssh "$VPS_USER@$VPS_IP" "pm2 status frontend && pm2 logs frontend --lines 10"

echo "✨ Deployment complete! Your app is ready at https://leadscraper.freelanceleadsapp.tech"
