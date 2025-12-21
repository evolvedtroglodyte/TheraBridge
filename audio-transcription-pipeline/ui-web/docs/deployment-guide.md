# Deployment Guide

Complete guide for deploying the Audio Transcription Web UI to various hosting platforms.

## Table of Contents

- [Overview](#overview)
- [Docker Compose (Local/Self-Hosted)](#docker-compose-localself-hosted)
- [Railway Deployment](#railway-deployment)
- [Fly.io Deployment](#flyio-deployment)
- [Platform Comparison](#platform-comparison)
- [Post-Deployment](#post-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)

## Overview

This application can be deployed to multiple platforms:

| Platform | Best For | Difficulty | Cost |
|----------|----------|------------|------|
| **Docker Compose** | Self-hosted, VPS, local production | Easy | Server costs only |
| **Railway** | Quick cloud deployment, simple scaling | Easy | ~$5-20/month + usage |
| **Fly.io** | Global edge deployment, auto-scaling | Moderate | Pay-per-use (~$0-10/month) |

### Deployment Checklist

Before deploying to any platform:

- ✅ Test locally first ([Local Setup Guide](local-setup.md))
- ✅ Have OpenAI API key ready
- ✅ Have HuggingFace token ready
- ✅ Understand your expected usage/traffic
- ✅ Review platform pricing
- ✅ Prepare custom domain (optional)

## Docker Compose (Local/Self-Hosted)

Best for: VPS deployment, self-hosted solutions, or local production-like testing.

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ RAM
- Ubuntu/Debian server (or equivalent)

### Installation

#### 1. Install Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

#### 2. Clone/Upload Project

```bash
# If cloning from git
git clone <your-repo-url>
cd audio-transcription-pipeline/ui-web

# Or upload files via scp/sftp
```

#### 3. Configure Environment

Create a `.env` file in the `deployment/` directory:

```bash
cd deployment
nano .env
```

Add your configuration:

```env
# API Keys (REQUIRED)
OPENAI_API_KEY=sk-proj-your-key-here
HUGGINGFACE_TOKEN=hf_your-token-here

# Optional: Override defaults
MAX_CONCURRENT_JOBS=3
LOG_LEVEL=INFO
```

#### 4. Build and Start

```bash
# Build images (first time or after code changes)
docker compose build

# Start services
docker compose up -d

# View logs
docker compose logs -f
```

The application will be available at:
- **Frontend**: http://your-server-ip
- **Backend API**: http://your-server-ip:8000
- **API Docs**: http://your-server-ip:8000/docs

#### 5. Verify Deployment

```bash
# Check service status
docker compose ps

# Test health endpoint
curl http://localhost:8000/health

# View backend logs
docker compose logs backend

# View frontend logs
docker compose logs frontend
```

### Docker Management

#### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose up -d --build
```

#### Stop Services

```bash
# Stop services (keeps data)
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove everything including volumes
docker compose down -v
```

#### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100
```

#### Scale Services

To handle more concurrent jobs, increase resources:

```yaml
# Edit docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Production Hardening (Docker)

For production deployments:

#### 1. Add Nginx Reverse Proxy

Create `nginx.conf`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
```

Add to `docker-compose.yml`:

```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl  # For HTTPS
    depends_on:
      - backend
      - frontend
```

#### 2. Enable HTTPS with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

#### 3. Set Up Backups

```bash
# Backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T backend tar -czf - /app/results > backup_$DATE.tar.gz
echo "Backup created: backup_$DATE.tar.gz"
EOF

chmod +x backup.sh

# Add to crontab (daily backups)
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

## Railway Deployment

Best for: Quick cloud deployment with minimal DevOps.

### Prerequisites

- Railway account ([railway.app](https://railway.app))
- Railway CLI (optional, recommended)

### Option 1: Deploy via Railway Dashboard (Easiest)

#### 1. Create New Project

1. Go to [railway.app/new](https://railway.app/new)
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect the configuration

#### 2. Configure Environment Variables

In the Railway dashboard:

1. Go to your project → Variables tab
2. Add the following variables:

```
OPENAI_API_KEY=sk-proj-your-key-here
HUGGINGFACE_TOKEN=hf_your-token-here
NODE_ENV=production
MAX_CONCURRENT_JOBS=3
LOG_LEVEL=INFO
```

#### 3. Deploy

Railway will automatically:
- Build your application
- Deploy to production
- Generate a public URL

Access your app at the provided Railway URL (e.g., `your-app.railway.app`)

### Option 2: Deploy via Railway CLI

#### 1. Install Railway CLI

```bash
# macOS
brew install railway

# Linux/WSL
curl -fsSL https://railway.app/install.sh | sh

# Verify installation
railway --version
```

#### 2. Login

```bash
railway login
```

This opens a browser for authentication.

#### 3. Initialize Project

```bash
# Navigate to ui-web directory
cd /path/to/audio-transcription-pipeline/ui-web

# Initialize Railway project
railway init
```

Select "Create new project" and give it a name.

#### 4. Set Environment Variables

```bash
# Set required variables
railway variables set OPENAI_API_KEY=sk-proj-your-key-here
railway variables set HUGGINGFACE_TOKEN=hf_your-token-here
railway variables set NODE_ENV=production
railway variables set MAX_CONCURRENT_JOBS=3
railway variables set LOG_LEVEL=INFO
```

#### 5. Deploy

```bash
# Deploy to Railway
railway up

# View logs
railway logs

# Open in browser
railway open
```

### Railway Configuration

The deployment uses `deployment/railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "npm install && npm run build"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Railway Management

#### View Logs

```bash
# Via CLI
railway logs

# Via Dashboard
# Go to project → Deployments → Click deployment → Logs tab
```

#### Update Deployment

```bash
# Push changes to GitHub (if connected to repo)
git push

# Or redeploy via CLI
railway up
```

#### Custom Domain

1. Go to Railway Dashboard → Settings → Domains
2. Click "Add Domain"
3. Enter your domain (e.g., `transcribe.example.com`)
4. Update DNS records as instructed
5. Railway will automatically provision SSL certificate

#### Scale Resources

Railway auto-scales based on usage. To set limits:

1. Go to Settings → Resource Limits
2. Set CPU and Memory limits
3. Monitor usage in Metrics tab

### Railway Pricing

- **Free Tier**: $5 credit/month (executes ~140 hours)
- **Developer Plan**: $5/month + usage ($0.000231/GB-hour memory, $0.000463/vCPU-hour)
- **Team Plan**: $20/month + usage

Estimated costs for light usage:
- ~100 transcriptions/month: $5-10/month
- ~500 transcriptions/month: $10-20/month

Monitor usage at: Dashboard → Usage tab

## Fly.io Deployment

Best for: Global edge deployment, auto-scaling, pay-per-use.

### Prerequisites

- Fly.io account ([fly.io](https://fly.io))
- flyctl CLI
- Credit card (for billing, but free tier available)

### Installation

#### 1. Install flyctl

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Verify installation
flyctl version
```

#### 2. Login

```bash
flyctl auth login
```

Opens browser for authentication.

### Deployment Steps

#### 1. Navigate to Project

```bash
cd /path/to/audio-transcription-pipeline/ui-web
```

#### 2. Launch App

```bash
# Initialize Fly.io app
flyctl launch

# Follow prompts:
# - App name: audio-transcription (or your choice)
# - Region: Choose closest to your users
# - PostgreSQL: No (not needed)
# - Redis: No (not needed)
# - Deploy now: No (we need to set secrets first)
```

This creates `fly.toml` configuration file.

#### 3. Set Secrets

```bash
# Set API keys as secrets (encrypted)
flyctl secrets set OPENAI_API_KEY=sk-proj-your-key-here
flyctl secrets set HUGGINGFACE_TOKEN=hf_your-token-here
```

#### 4. Configure fly.toml

The deployment uses `deployment/fly.toml`. Ensure it's configured:

```toml
app = "audio-transcription"  # Your app name
primary_region = "sjc"       # Your chosen region

[build]
  dockerfile = "../backend/Dockerfile"

[env]
  API_HOST = "0.0.0.0"
  API_PORT = "8000"
  MAX_CONCURRENT_JOBS = "3"
  LOG_LEVEL = "INFO"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[http_service.checks]]
  interval = "15s"
  timeout = "5s"
  grace_period = "10s"
  method = "GET"
  path = "/health"
```

#### 5. Deploy

```bash
# Deploy application
flyctl deploy

# Wait for deployment to complete
# Access at: https://your-app-name.fly.dev
```

### Fly.io Management

#### View Status

```bash
# App status
flyctl status

# View logs
flyctl logs

# SSH into machine
flyctl ssh console
```

#### Update Application

```bash
# After code changes
flyctl deploy

# Force rebuild
flyctl deploy --build-only
```

#### Scale Resources

```bash
# Scale VM size
flyctl scale vm shared-cpu-1x  # 256MB RAM (free tier)
flyctl scale vm shared-cpu-2x  # 512MB RAM
flyctl scale vm shared-cpu-4x  # 1GB RAM

# Scale regions (multi-region deployment)
flyctl regions add lax sea  # Add LA and Seattle

# Set machine count
flyctl scale count 2  # Run 2 machines
```

#### Monitor Performance

```bash
# View metrics
flyctl dashboard metrics

# View current machines
flyctl machine list

# View machine status
flyctl machine status <machine-id>
```

#### Custom Domain

```bash
# Add custom domain
flyctl certs add transcribe.example.com

# View certificate status
flyctl certs show transcribe.example.com

# Update DNS records as instructed
# A record: @ -> <your-app-ipv6>
# AAAA record: @ -> <your-app-ipv6>
```

### Fly.io Configuration Details

#### Auto-Scaling

Fly.io automatically:
- Stops machines when idle (saves money)
- Starts machines on first request
- Scales up during high traffic

Configure in `fly.toml`:

```toml
[http_service]
  auto_stop_machines = true    # Stop when idle
  auto_start_machines = true   # Start on request
  min_machines_running = 0     # No always-on machines (free)
```

#### Health Checks

Health checks ensure your app is running:

```toml
[[http_service.checks]]
  interval = "15s"      # Check every 15 seconds
  timeout = "5s"        # Timeout after 5 seconds
  method = "GET"
  path = "/health"
```

### Fly.io Pricing

- **Free Tier**:
  - 3 shared-cpu-1x VMs (256MB RAM each)
  - 160GB bandwidth/month
  - Enough for development and light production

- **Paid Usage**:
  - Shared CPU: $0.0000022/second (~$5.70/month if always-on)
  - Memory: $0.0000004/MB/second (~$0.70/GB/month)
  - Bandwidth: $0.02/GB after free tier

**Auto-scaling saves money**: With `auto_stop_machines=true`, you only pay when actually processing requests.

Estimated costs:
- Development: Free
- Light usage (100 transcriptions/month): $0-5/month
- Heavy usage (1000+ transcriptions/month): $10-20/month

Monitor usage:
```bash
flyctl dashboard billing
```

## Platform Comparison

### Feature Comparison

| Feature | Docker Compose | Railway | Fly.io |
|---------|---------------|---------|--------|
| **Setup Difficulty** | Moderate | Easy | Moderate |
| **Deployment Speed** | Manual | Instant | ~2 minutes |
| **Auto-Scaling** | No | Yes | Yes |
| **Global CDN** | No | Limited | Yes |
| **WebSocket Support** | Yes | Yes | Yes |
| **Custom Domain** | Manual | Easy | Easy |
| **SSL/HTTPS** | Manual | Automatic | Automatic |
| **Monitoring** | DIY | Built-in | Built-in |
| **Logs** | Docker logs | Dashboard | CLI + Dashboard |
| **Backup** | Manual | Automatic | Manual |

### Cost Comparison (Monthly Estimates)

For **100 transcriptions/month** (~5 hours processing):

| Platform | Cost | Includes |
|----------|------|----------|
| **Docker (VPS)** | $5-10 | DigitalOcean Droplet, Linode VPS |
| **Railway** | $5-10 | Hosting, auto-deploy, monitoring |
| **Fly.io** | $0-5 | Free tier, auto-scaling |

For **1000 transcriptions/month** (~50 hours processing):

| Platform | Cost | Includes |
|----------|------|----------|
| **Docker (VPS)** | $10-20 | Larger VPS instance |
| **Railway** | $15-30 | Higher resource usage |
| **Fly.io** | $10-20 | Scaled resources |

> **Note**: Add OpenAI API costs (Whisper API usage) separately. Estimate ~$0.006/minute of audio.

### Recommendation by Use Case

| Use Case | Recommended Platform |
|----------|---------------------|
| Personal project, low traffic | **Fly.io** (free tier) |
| MVP, quick launch | **Railway** (easiest) |
| Self-hosted, full control | **Docker Compose** |
| Production, high availability | **Fly.io** (multi-region) |
| Team collaboration | **Railway** (team features) |
| Cost-sensitive, high volume | **Docker Compose** (VPS) |

## Post-Deployment

### Verify Deployment

After deploying to any platform:

#### 1. Test Health Endpoint

```bash
curl https://your-app-url.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "pipeline_path": "../../src/pipeline.py",
  "upload_dir": "./uploads",
  "results_dir": "./results"
}
```

#### 2. Test File Upload

1. Navigate to your deployment URL
2. Upload a small test file (< 1 minute audio)
3. Verify real-time progress updates
4. Confirm transcription completes successfully

#### 3. Test WebSocket Connection

Open browser DevTools (F12) → Console:
- Should see: `WebSocket connected for job: <job-id>`
- No connection errors

#### 4. Check API Documentation

Navigate to: `https://your-app-url.com/docs`
- Swagger UI should load
- All endpoints visible
- Can test endpoints directly

### Security Considerations

#### Environment Variables

Never commit secrets to git:
```bash
# Ensure these are in .gitignore
backend/.env
frontend/.env.local
deployment/.env
```

#### CORS Configuration

Restrict CORS to your frontend domain:
```env
# In production
CORS_ORIGINS=https://your-frontend-domain.com

# Multiple domains
CORS_ORIGINS=https://app.example.com,https://www.example.com
```

#### Rate Limiting

Consider adding rate limiting for public deployments:
```python
# In backend/app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# On routes
@limiter.limit("10/minute")
@router.post("/upload")
async def upload_audio(...):
    ...
```

#### File Upload Restrictions

Ensure upload limits are reasonable:
```env
MAX_UPLOAD_SIZE_MB=100  # Adjust based on needs
```

## Monitoring & Maintenance

### Logging

#### Railway Logs

```bash
# Via CLI
railway logs --tail 100

# Via Dashboard
# Project → Deployments → Select deployment → Logs tab
```

#### Fly.io Logs

```bash
# Live tail
flyctl logs

# Filter by level
flyctl logs --level error

# View specific machine
flyctl logs --machine <machine-id>
```

#### Docker Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last hour
docker compose logs --since 1h

# Save to file
docker compose logs > logs.txt
```

### Monitoring Metrics

#### System Metrics

Railway/Fly.io Dashboard shows:
- CPU usage
- Memory usage
- Request rate
- Response times
- Error rates

#### Application Metrics

Monitor in logs:
- Job queue length
- Processing times
- API latency
- Error counts

#### Set Up Alerts

**Railway**: Settings → Notifications
- Deployment failures
- Resource limits
- Error rate spikes

**Fly.io**: `fly.toml` health checks alert automatically

### Backup Strategy

#### Results Backup (Important)

Transcription results should be backed up regularly:

**Docker**:
```bash
# Backup script
tar -czf backup_$(date +%Y%m%d).tar.gz backend/results/
```

**Railway/Fly.io**:
- Store results in external storage (AWS S3, Cloudflare R2)
- Or download periodically via API

#### Database Backup (If Added Later)

If you add a database:
```bash
# Railway: Automatic backups included
# Fly.io: Use volumes with snapshots
flyctl volumes create results_data --size 10
```

### Scaling Strategies

#### Vertical Scaling (More Resources)

**Docker**: Edit `docker-compose.yml` resource limits
**Railway**: Auto-scales, or upgrade plan
**Fly.io**: `flyctl scale vm shared-cpu-4x`

#### Horizontal Scaling (More Instances)

**Docker**: Use Docker Swarm or Kubernetes
**Railway**: Increase replicas in dashboard
**Fly.io**: `flyctl scale count 3`

#### Job Queue Scaling

Increase concurrent jobs:
```env
MAX_CONCURRENT_JOBS=5  # Default: 3
```

> **Warning**: More concurrent jobs = higher memory usage and API costs.

### Updating Your Deployment

#### Update Process

1. **Test locally first**
2. **Commit changes** to git
3. **Deploy update**:
   - **Railway**: Auto-deploys on git push (if connected)
   - **Fly.io**: `flyctl deploy`
   - **Docker**: `docker compose up -d --build`

#### Rollback Strategy

**Railway**: Dashboard → Deployments → Select previous deployment → Redeploy
**Fly.io**: Keep previous releases, rollback with:
```bash
flyctl releases list
flyctl deploy --image registry.fly.io/app-name:v123
```
**Docker**: Keep tagged images:
```bash
docker tag myapp:latest myapp:v1.0
docker compose down && docker compose up -d --build
```

## Troubleshooting Deployments

### Common Issues

#### Build Failures

**Symptom**: Deployment fails during build

**Solutions**:
- Check build logs for specific errors
- Verify Dockerfile syntax
- Ensure all dependencies in requirements.txt
- Check Python/Node versions match local

#### Out of Memory

**Symptom**: App crashes with "killed" or OOM errors

**Solutions**:
- Reduce `MAX_CONCURRENT_JOBS`
- Increase VM memory size
- Monitor memory usage in logs
- Optimize pipeline code

#### WebSocket Not Working

**Symptom**: No real-time updates

**Solutions**:
- Ensure WebSocket support enabled (all platforms support it)
- Check CORS settings include frontend domain
- Verify WSS (not WS) for HTTPS deployments
- Check browser console for connection errors

#### Slow Transcription

**Symptom**: Processing takes very long

**Solutions**:
- Check OpenAI API status
- Verify network connectivity
- Monitor API latency in logs
- Consider GPU deployment for large files

## Next Steps

After successful deployment:

1. **Set up monitoring** and alerts
2. **Configure custom domain** (optional)
3. **Set up automated backups**
4. **Review and optimize costs**
5. **Test at scale** with real workloads
6. **Document your specific deployment** for team reference

## Support Resources

- **Railway**: [docs.railway.app](https://docs.railway.app)
- **Fly.io**: [fly.io/docs](https://fly.io/docs)
- **Docker**: [docs.docker.com](https://docs.docker.com)

---

**Deployment complete!** Your Audio Transcription UI is now live and ready for production use.
