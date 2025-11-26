# Docker Deployment Guide

This guide covers deploying the Internal Training System using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Sufficient disk space (minimum 10GB recommended)
- Required API keys (OpenAI, Agora, AWS S3)

## Quick Start (Development)

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/InternalTrainingSystem-Fresh
   ```

2. **Create deployment config:**
   ```bash
   cp deployment/config.example.toml deployment/config.toml
   # Edit deployment/config.toml with customer-specific credentials
   ```

   The config file contains every parameter (database, AWS S3, OpenAI, Agora, Microsoft TTS, ElevenLabs, etc).  
   When you run `docker-start.sh`, it will automatically render the `.env` file that docker-compose consumes.

3. **Start development environment:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

5. **Stop the application:**
   ```bash
   docker-compose down
   ```

## Configuration Automation

To hand over a true “one-click” Docker deployment:

1. Copy `deployment/config.example.toml` to `deployment/config.toml` and populate it with the customer’s credentials (database, AWS S3 bucket, OpenAI key, Agora settings, Microsoft TTS, ElevenLabs, etc).
2. Run `./docker-start.sh dev` or `./docker-start.sh prod`. The script automatically calls `python3 deployment/render_env.py`, which converts the TOML config into the `.env` file that docker-compose uses for PostgreSQL, the FastAPI backend, and the frontend build arguments.
3. Distribute only the filled `deployment/config.toml` plus the repository. Your customer simply executes the same script and receives the identical stack (database included) in a single command.

You can also regenerate the `.env` manually if needed:

```bash
python3 deployment/render_env.py --config deployment/config.toml --output .env
```

> `.env` remains git-ignored so secrets never leave the deployment machine. The TOML template is the only file you version-control.

**Debian mirror override:** For regions where `deb.debian.org` is blocked/slow, set `[docker] apt_mirror = "mirrors.aliyun.com"` (or any mirror) in `deployment/config.toml`. The backend Docker image will rewrite `/etc/apt/sources.list` before every `apt-get update`.

## Production Deployment

### Step 1: Environment Configuration

Create a production `deployment/config.toml` file:

```bash
cp deployment/config.example.toml deployment/config.toml
```

Fill in every secret (database credentials, AWS bucket, OpenAI key, Agora config, Microsoft TTS, ElevenLabs, etc).  
The `deployment/render_env.py` helper (automatically invoked by `docker-start.sh`) converts this TOML file into the `.env`
format that docker-compose uses for both dev and prod stacks.

> Tip: `cors_origins` accepts a TOML array, e.g. `cors_origins = ["https://yourdomain.com", "https://app.yourdomain.com"]`.

### Step 2: SSL Certificates (Optional but Recommended)

If you want HTTPS support:

1. **Obtain SSL certificates** (Let's Encrypt, CloudFlare, or your provider)

2. **Place certificates in nginx/ssl directory:**
   ```bash
   mkdir -p nginx/ssl
   cp /path/to/your/cert.pem nginx/ssl/
   cp /path/to/your/key.pem nginx/ssl/
   ```

3. **Update nginx/nginx.prod.conf:**
   - Uncomment the HTTPS server block (lines starting with #)
   - Update `server_name` with your domain
   - Uncomment the HTTP to HTTPS redirect

### Step 3: Build and Deploy

1. **Build images:**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

2. **Start production services:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Check service status:**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

4. **View logs:**
   ```bash
   # All services
   docker-compose -f docker-compose.prod.yml logs -f

   # Specific service
   docker-compose -f docker-compose.prod.yml logs -f backend
   ```

### Step 4: Initialize Database

The database migrations run automatically on backend startup. To manually run migrations:

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Step 5: Verify Deployment

1. **Health checks:**
   ```bash
   curl http://localhost/health        # Frontend health
   curl http://localhost/api/health     # Backend health (proxied)
   ```

2. **Check all containers are running:**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

   You should see:
   - `its-postgres-prod` (running)
   - `its-backend-prod` (running, possibly 2 replicas)
   - `its-frontend-builder` (exited after build)
   - `its-nginx-prod` (running)

## Architecture

### Development Setup (docker-compose.yml)
```
┌─────────────┐
│  Frontend   │ :80 (nginx)
│   (React)   │
└─────────────┘
       │
       ▼
┌─────────────┐
│   Backend   │ :8000 (FastAPI)
│  (Python)   │
└─────────────┘
       │
       ▼
┌─────────────┐
│  PostgreSQL │ :5432
└─────────────┘
```

### Production Setup (docker-compose.prod.yml)
```
                    ┌─────────────┐
Internet ──────────▶│    Nginx    │ :80, :443
                    │ (Reverse    │
                    │  Proxy)     │
                    └─────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
          ▼                                 ▼
   ┌─────────────┐                   ┌─────────────┐
   │  Frontend   │                   │   Backend   │
   │   Static    │                   │(Load Bal.)  │
   │   Files     │                   │  Replicas   │
   └─────────────┘                   └─────────────┘
                                            │
                                            ▼
                                     ┌─────────────┐
                                     │ PostgreSQL  │
                                     └─────────────┘
```

## Maintenance

### Backup Database

```bash
# Backup
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U postgres training_system > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U postgres training_system < backup_file.sql
```

### Backup ChromaDB Vector Store

```bash
# The ChromaDB data is stored in a Docker volume
docker run --rm -v its-prod_chroma_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/chroma_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up --build -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Scale Backend

To adjust the number of backend replicas:

```bash
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

Or edit `docker-compose.prod.yml` and change `replicas: 2` to your desired number.

### View Resource Usage

```bash
docker stats
```

## Troubleshooting

### Backend won't start

**Check logs:**
```bash
docker-compose -f docker-compose.prod.yml logs backend
```

**Common issues:**
- Database connection: Verify DATABASE_URL in .env
- Missing API keys: Check all required environment variables
- Port conflicts: Ensure ports 80, 443 are available

### Frontend not loading

**Check nginx logs:**
```bash
docker-compose -f docker-compose.prod.yml logs nginx
```

**Verify build completed:**
```bash
docker-compose -f docker-compose.prod.yml logs frontend
```

### Database connection errors

**Test database:**
```bash
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d training_system -c "SELECT 1;"
```

**Check health:**
```bash
docker-compose -f docker-compose.prod.yml exec postgres pg_isready
```

### Clear everything and start fresh

```bash
# Stop and remove all containers, volumes
docker-compose -f docker-compose.prod.yml down -v

# Remove images
docker-compose -f docker-compose.prod.yml down --rmi all

# Rebuild from scratch
docker-compose -f docker-compose.prod.yml up --build -d
```

## Security Considerations

### Production Checklist

- [ ] Use strong, unique passwords for all services
- [ ] Set SECRET_KEY to a secure random value
- [ ] Configure SSL certificates for HTTPS
- [ ] Update `cors_origins` in deployment/config.toml to match your domain
- [ ] Don't expose PostgreSQL port (5432) to internet
- [ ] Enable firewall rules (only allow 80, 443)
- [ ] Regularly update Docker images
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Monitor resource usage

### Environment Variables Security

**Never commit .env files to git!**

The `.env` file contains sensitive credentials. It's already in `.gitignore`, but verify:

```bash
git status  # Should NOT show .env file
```

## Performance Tuning

### Backend Replicas

For high traffic, increase backend replicas in `docker-compose.prod.yml`:

```yaml
deploy:
  replicas: 4  # Increase based on CPU cores
```

### Database Optimization

Adjust PostgreSQL resources in `docker-compose.prod.yml`:

```yaml
postgres:
  deploy:
    resources:
      limits:
        cpus: '2.0'    # Increase if needed
        memory: 4G     # Increase if needed
```

### Nginx Caching

For better performance, consider adding nginx caching:

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    # ... other config
}
```

## Monitoring

### Health Checks

All services include health checks. Check status:

```bash
docker-compose -f docker-compose.prod.yml ps
```

Healthy services show "healthy" in STATUS column.

### Logs

```bash
# Follow all logs
docker-compose -f docker-compose.prod.yml logs -f

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100

# Specific service
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Resource Monitoring

```bash
# Real-time stats
docker stats

# Disk usage
docker system df
```

## Cloud Deployment

### AWS EC2

1. Launch EC2 instance (t3.medium or larger)
2. Install Docker and Docker Compose
3. Clone repository
4. Configure security groups (allow 80, 443, 22)
5. Follow production deployment steps above
6. Consider using AWS RDS instead of containerized PostgreSQL
7. Use AWS S3 for file storage (already configured)

### DigitalOcean Droplet

1. Create Droplet with Docker pre-installed
2. Add domain and configure DNS
3. Clone repository
4. Follow production deployment steps above
5. Use DigitalOcean Spaces for file storage (S3-compatible)

### Google Cloud Run / Azure Container Instances

These platforms require splitting services into separate deployments. The current Docker Compose setup is optimized for VM-based deployment (AWS EC2, DigitalOcean, etc.).

## Support

For issues or questions:
- Check logs first: `docker-compose logs`
- Review this documentation
- Check Docker and container status
- Verify environment variables
