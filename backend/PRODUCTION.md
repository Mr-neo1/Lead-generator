# Automated Lead Engine - Production Deployment Guide

## Quick Start (Docker - Recommended)

### Prerequisites
- Docker Desktop installed and running
- At least 4GB RAM available

### 1. Start All Services
```bash
cd backend
docker-compose up -d --build
```

This starts:
- **PostgreSQL** database on port 5432
- **Redis** queue on port 6379
- **FastAPI** backend on port 8000
- **12 Worker processes** (2 discovery, 6 details, 2 analysis, 2 demo)

### 2. Start Frontend
```bash
# In a new terminal, from project root
npm install
npm run dev
```

Frontend runs on http://localhost:3000

### 3. Access the System
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Demo Sites**: http://localhost:8000/demo-sites/

---

## API Endpoints

### Jobs
- `POST /api/jobs` - Create new scraping job
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{job_id}` - Get job details
- `DELETE /api/jobs/{job_id}` - Delete job
- `POST /api/jobs/{job_id}/restart` - Restart failed job

### Leads
- `GET /api/leads` - Get all leads
- `GET /api/leads/{lead_id}` - Get lead details
- `GET /api/leads/export?lead_type=NO_WEBSITE&min_score=5` - Export as CSV
- `POST /api/leads/{lead_id}/generate-demo` - Generate demo site

### System
- `GET /api/stats` - Dashboard statistics
- `GET /api/queue/status` - Queue status (Redis required)
- `GET /` - Health check

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://leaduser:leadpassword@db:5432/leadengine` | Database connection |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `USE_REDIS` | `true` | Enable queue system |

### Worker Configuration (docker-compose.yml)

```yaml
# Adjust replicas based on VPS resources
worker_discovery:
  deploy:
    replicas: 2  # Browser workers (memory intensive)

worker_details:
  deploy:
    replicas: 6  # HTTP workers (lightweight)

worker_analysis:
  deploy:
    replicas: 2

worker_demo:
  deploy:
    replicas: 2
```

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                          │
│              http://localhost:3000                           │
└────────────────────────────┬─────────────────────────────────┘
                             │ API Calls
┌────────────────────────────▼─────────────────────────────────┐
│                    FastAPI Backend                            │
│              http://localhost:8000                           │
│                                                              │
│  POST /api/jobs → Creates job → Enqueues discovery tasks     │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                    Redis Queue                                │
│                                                              │
│  Queues: discovery → details → analysis → demo               │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                    RQ Workers                                 │
│                                                              │
│  Discovery (2x) → Details (6x) → Analysis (2x) → Demo (2x)  │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐           │
│  │ Playwright  │  │   aiohttp   │  │  Generate  │           │
│  │   Browser   │  │   Requests  │  │    HTML    │           │
│  └─────────────┘  └─────────────┘  └────────────┘           │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                   PostgreSQL Database                         │
│                                                              │
│  Tables: businesses, lead_analysis, demo_sites, scraping_jobs│
└──────────────────────────────────────────────────────────────┘
```

---

## Processing Pipeline

### Stage 1: Discovery (Playwright)
- Opens headless browser
- Navigates to Google Maps
- Scrolls to load results
- Extracts: place_id, name, maps_url
- Queues business for detail fetch

### Stage 2: Detail Fetch (HTTP)
- Fetches Maps page via HTTP
- Extracts: website, phone, rating, reviews, category, address
- Queues for analysis

### Stage 3: Analysis
- Checks website SSL, mobile-friendliness, load time
- Calculates lead score (0-8)
- Classifies lead type: NO_WEBSITE, WEBSITE_REDESIGN, NORMAL
- High-score leads (≥6) queued for demo generation

### Stage 4: Demo Generation
- Creates professional HTML demo site
- Tailored to business category
- Stored in /demo-sites/

---

## Lead Scoring Model

| Factor | Points |
|--------|--------|
| No website | +4 |
| Rating > 4.0 | +2 |
| Reviews > 20 | +1 |
| Phone available | +1 |

**Total: 0-8 points**

High Priority: Score ≥ 6

---

## Expected Performance (4GB VPS)

| Metric | Daily Estimate |
|--------|----------------|
| Businesses scraped | 10,000 - 25,000 |
| Qualified leads | 3,000 - 8,000 |
| Demo sites generated | 500 - 2,000 |

---

## Troubleshooting

### Check worker logs
```bash
docker-compose logs -f worker_discovery
docker-compose logs -f worker_details
```

### Check queue status
```bash
curl http://localhost:8000/api/queue/status
```

### Reset database
```bash
docker-compose down -v
docker-compose up -d
```

### View all containers
```bash
docker-compose ps
```

---

## Production Deployment (VPS)

### 1. Clone repository
```bash
git clone <your-repo>
cd leads
```

### 2. Configure environment
```bash
# Create .env file in backend/
DATABASE_URL=postgresql://leaduser:leadpassword@db:5432/leadengine
REDIS_URL=redis://redis:6379/0
USE_REDIS=true
```

### 3. Deploy with Docker
```bash
cd backend
docker-compose up -d --build
```

### 4. Set up reverse proxy (Nginx)
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name app.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. SSL with Certbot
```bash
sudo certbot --nginx -d api.yourdomain.com -d app.yourdomain.com
```

---

## License

MIT
