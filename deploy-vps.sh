#!/bin/bash
set -e

# VPS Deployment Script for Lead Engine
# Usage: ./deploy-vps.sh

VPS_IP="209.38.120.251"
VPS_USER="root"
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
APP_LOGIN_PASSWORD=\"Abha009885@#@@\"
APP_LOGIN_SECRET=\".tI-~<y3H|.k[Lllz7[3]B)K4;iERZq{FL\$BU=/)0yAJDFb#uZV<l|j+oGn#DeQ{\"
ENVEOF"

# Step 6: Restart PM2
echo "🔄 Restarting application..."
ssh "$VPS_USER@$VPS_IP" "pm2 restart frontend && sleep 3"

# Step 7: Verify deployment
echo "✅ Verifying deployment..."
ssh "$VPS_USER@$VPS_IP" "pm2 status frontend && pm2 logs frontend --lines 10"

echo "✨ Deployment complete! Your app is ready at https://leadscraper.freelanceleadsapp.tech"
