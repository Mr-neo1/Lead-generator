#!/bin/bash
set -e

echo "=========================================="
echo "   Lead Generator - Full VPS Deployment  "
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

DOMAIN=${DOMAIN:-leadscraper.freelancleadsapp.tech}

# Step 1: System Update
echo ""
echo "Step 1: Updating system..."
apt update && apt upgrade -y
print_status "System updated"

# Step 2: Install Docker
echo ""
echo "Step 2: Installing Docker..."
apt install -y docker.io docker-compose-v2 git curl
systemctl enable docker
systemctl start docker
print_status "Docker installed and started"

# Step 3: Install Node.js 20
echo ""
echo "Step 3: Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
print_status "Node.js $(node -v) installed"

# Step 4: Install PM2
echo ""
echo "Step 4: Installing PM2..."
npm install -g pm2
print_status "PM2 installed"

# Step 5: Clone Repository
echo ""
echo "Step 5: Setting up project..."
cd /root

if [ -d "Lead-generator" ]; then
    print_warning "Lead-generator folder exists, pulling latest..."
    cd Lead-generator
    git pull
else
    git clone https://github.com/Mr-neo1/Lead-generator.git
    cd Lead-generator
fi
print_status "Repository ready"

# Step 6: Setup Environment and Backend
echo ""
echo "Step 6: Setting up environment and backend..."
cd /root/Lead-generator/backend

# Create single root .env file
cat > /root/Lead-generator/.env << EOF
NEXT_PUBLIC_API_URL=https://${DOMAIN}
NEXT_PUBLIC_API_KEY=${API_KEY:-CHANGE_ME_TO_SECURE_API_KEY}
APP_URL=https://${DOMAIN}
APP_LOGIN_USERNAME=admin
APP_LOGIN_PASSWORD=${APP_LOGIN_PASSWORD:-change-me}
APP_LOGIN_SECRET=${APP_LOGIN_SECRET:-replace-with-a-long-random-secret}
DATABASE_URL=postgresql://leaduser:leadpassword@db:5432/leadengine
REDIS_URL=redis://redis:6379/0
USE_REDIS=true
API_KEY=${API_KEY:-CHANGE_ME_TO_SECURE_API_KEY}
CORS_ORIGINS=https://${DOMAIN},http://localhost:3000
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EOF

print_status "Root .env created"

# Start backend with Docker
echo "Building and starting backend containers (this may take 5-10 minutes)..."
docker compose -f docker-compose.light.yml down 2>/dev/null || true
docker compose -f docker-compose.light.yml up -d --build

print_status "Backend containers started"

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 10

# Check if API is responding
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        print_status "Backend API is ready!"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

# Step 7: Setup Frontend
echo ""
echo "Step 7: Setting up Frontend..."
cd /root/Lead-generator

# Install dependencies and build
echo "Installing frontend dependencies..."
npm install

echo "Building frontend (this may take 2-3 minutes)..."
npm run build

# Stop existing PM2 process if exists
pm2 delete leads-frontend 2>/dev/null || true

# Start frontend with PM2
pm2 start npm --name "leads-frontend" -- start -- -p 3000

# Save PM2 config and setup startup
pm2 save
pm2 startup systemd -u root --hp /root

print_status "Frontend started with PM2"

# Step 8: Summary
echo ""
echo "=========================================="
echo "         DEPLOYMENT COMPLETE!            "
echo "=========================================="
echo ""
echo "Your Lead Generator is now running:"
echo ""
echo -e "  ${GREEN}Dashboard:${NC}  https://${DOMAIN}"
echo -e "  ${GREEN}API Docs:${NC}   https://${DOMAIN}/docs"
echo -e "  ${GREEN}API Health:${NC} https://${DOMAIN}/health"
echo ""
echo "Useful commands:"
echo "  - View frontend logs:  pm2 logs leads-frontend"
echo "  - View backend logs:   cd /root/Lead-generator/backend && docker compose -f docker-compose.light.yml logs -f"
echo "  - Restart frontend:    pm2 restart leads-frontend"
echo "  - Restart backend:     cd /root/Lead-generator/backend && docker compose -f docker-compose.light.yml restart"
echo ""
echo "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in /root/Lead-generator/.env if needed."
echo ""
