# Nginx Configuration

This directory contains nginx configuration for production deployment.

## Files

- `nginx.prod.conf` - Production nginx configuration with reverse proxy and load balancing
- `ssl/` - Directory for SSL certificates (not tracked in git)

## SSL Certificate Setup

### Option 1: Let's Encrypt (Free, Recommended)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy to nginx/ssl directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# Set permissions
sudo chmod 644 nginx/ssl/cert.pem
sudo chmod 600 nginx/ssl/key.pem
```

### Option 2: Self-Signed Certificate (Development/Testing)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

**Note:** Self-signed certificates will show browser warnings. Only use for development.

### Option 3: Commercial Certificate

If you purchased an SSL certificate:

1. Place your certificate file as `nginx/ssl/cert.pem`
2. Place your private key as `nginx/ssl/key.pem`
3. Ensure proper permissions (cert: 644, key: 600)

## Enabling HTTPS

After placing SSL certificates:

1. Edit `nginx.prod.conf`:
   - Uncomment the HTTPS server block (search for "# server {")
   - Update `server_name` with your actual domain
   - Uncomment the HTTP to HTTPS redirect

2. Restart nginx:
   ```bash
   docker-compose -f docker-compose.prod.yml restart nginx
   ```

## Configuration Details

### Upstream Load Balancing

The configuration uses `least_conn` algorithm to distribute requests across backend replicas:

```nginx
upstream backend {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=30s;
}
```

### Security Headers

- `X-Frame-Options`: Prevents clickjacking
- `X-Content-Type-Options`: Prevents MIME-type sniffing
- `X-XSS-Protection`: Enables browser XSS protection
- `Content-Security-Policy`: Controls resource loading

### Compression

Gzip compression is enabled for text-based assets to reduce bandwidth.

### Caching

Static assets (CSS, JS, images) are cached for 1 year with immutable cache control.

### API Proxy

All requests to `/api/*` are proxied to the backend service with proper headers and timeouts.

## Testing Configuration

Test nginx configuration before restarting:

```bash
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

## Troubleshooting

### 502 Bad Gateway

- Backend service is not running
- Check backend logs: `docker-compose -f docker-compose.prod.yml logs backend`
- Verify backend health: `curl http://localhost:8000/api/v1/health`

### SSL Certificate Errors

- Verify certificate files exist in `nginx/ssl/`
- Check file permissions (cert: 644, key: 600)
- Test configuration: `docker-compose exec nginx nginx -t`

### WebSocket Connection Failed

- Ensure `/ws/` location block is uncommented
- Check if upgrade headers are being passed correctly
- Verify firewall allows WebSocket connections
