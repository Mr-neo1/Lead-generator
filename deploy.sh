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

# Step 6: Setup Backend
echo ""
echo "Step 6: Setting up Backend..."
cd /root/Lead-generator/backend

# Create .env file
cat > .env << 'EOF'
DATABASE_URL=postgresql://leaduser:leadpassword@db:5432/leadengine
REDIS_URL=redis://redis:6379/0
USE_REDIS=true
TELEGRAM_BOT_TOKEN=8494513906:AAHi-b3iDkRwP6IthiW6Aw4b-STrZhLliP8
TELEGRAM_CHAT_ID=1082069915
EOF

print_status "Backend .env created"

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

# Get VPS public IP
VPS_IP=$(curl -s ifconfig.me)

# Create frontend .env
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://${VPS_IP}:8000
EOF

print_status "Frontend .env.local created with API URL: http://${VPS_IP}:8000"

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
echo -e "  ${GREEN}Dashboard:${NC}  http://${VPS_IP}:3000"
echo -e "  ${GREEN}API Docs:${NC}   http://${VPS_IP}:8000/docs"
echo -e "  ${GREEN}API Health:${NC} http://${VPS_IP}:8000/"
echo ""
echo "Useful commands:"
echo "  - View frontend logs:  pm2 logs leads-frontend"
echo "  - View backend logs:   cd /root/Lead-generator/backend && docker compose -f docker-compose.light.yml logs -f"
echo "  - Restart frontend:    pm2 restart leads-frontend"
echo "  - Restart backend:     cd /root/Lead-generator/backend && docker compose -f docker-compose.light.yml restart"
echo ""
echo "Telegram notifications are configured and will alert you for high-value leads!"
echo ""
