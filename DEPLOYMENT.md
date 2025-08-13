# 🚀 RLCF Framework - Production Deployment Guide

This guide provides comprehensive instructions for deploying the RLCF Framework to production environments.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Backend Deployment](#backend-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Database Setup](#database-setup)
- [Environment Configuration](#environment-configuration)
- [Security Considerations](#security-considerations)
- [Monitoring and Logging](#monitoring-and-logging)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 20.04 LTS or newer (recommended)
- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum, SSD recommended
- **Python**: 3.9+
- **Node.js**: 18.x LTS or newer
- **Database**: PostgreSQL 14+ (production) or SQLite (development)

### Required Software
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx postgresql postgresql-contrib
```

## Backend Deployment

### 1. Application Setup

```bash
# Clone repository
git clone <your-repo-url> /opt/rlcf
cd /opt/rlcf

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install production server
pip install gunicorn uvicorn[standard]
```

### 2. Environment Configuration

Create production environment file:
```bash
# /opt/rlcf/.env
DATABASE_URL=postgresql://rlcf_user:secure_password@localhost/rlcf_db
ADMIN_API_KEY=your-super-secure-admin-key-here
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### 3. Database Setup

```bash
# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE rlcf_db;
CREATE USER rlcf_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE rlcf_db TO rlcf_user;
GRANT ALL ON SCHEMA public TO rlcf_user;
\q
```

```bash
# Run database migrations
python -c "
import asyncio
from rlcf_framework.database import engine
from rlcf_framework import models

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

asyncio.run(init_db())
"
```

### 4. Systemd Service

Create systemd service file:
```bash
sudo nano /etc/systemd/system/rlcf-backend.service
```

```ini
[Unit]
Description=RLCF Framework Backend
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/rlcf
Environment=PATH=/opt/rlcf/venv/bin
EnvironmentFile=/opt/rlcf/.env
ExecStart=/opt/rlcf/venv/bin/gunicorn rlcf_framework.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Set permissions and start service
sudo chown -R www-data:www-data /opt/rlcf
sudo systemctl daemon-reload
sudo systemctl enable rlcf-backend
sudo systemctl start rlcf-backend
```

## Frontend Deployment

### 1. Build Application

```bash
cd /opt/rlcf/frontend

# Install dependencies
npm ci

# Create production build
npm run build
```

### 2. Nginx Configuration

Create Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/rlcf
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /path/to/your/certificate.pem;
    ssl_certificate_key /path/to/your/private-key.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Frontend static files
    location / {
        root /opt/rlcf/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API proxy
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # WebSocket endpoint
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/rlcf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Environment Configuration

### Frontend Environment Variables

Create `/opt/rlcf/frontend/.env.production`:
```bash
VITE_API_BASE_URL=https://your-domain.com/api
VITE_WS_URL=wss://your-domain.com/ws
VITE_ENVIRONMENT=production
```

### Backend Environment Variables

Update `/opt/rlcf/.env`:
```bash
DATABASE_URL=postgresql://rlcf_user:secure_password@localhost/rlcf_db
ADMIN_API_KEY=your-super-secure-admin-key-here
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

## Security Considerations

### 1. SSL/TLS Certificate

Using Let's Encrypt (recommended):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 2. Firewall Configuration

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 3. Database Security

```bash
# Secure PostgreSQL installation
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'strong_postgres_password';"

# Edit PostgreSQL configuration
sudo nano /etc/postgresql/14/main/pg_hba.conf
# Change 'trust' to 'md5' for local connections
```

### 4. API Key Management

- Use strong, randomly generated API keys
- Store sensitive data in environment variables
- Consider using a secrets management system for production

## Monitoring and Logging

### 1. Application Logs

```bash
# Backend logs
sudo journalctl -u rlcf-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Health Check Endpoint

The backend includes a health check at `/health`:
```bash
curl https://your-domain.com/api/health
```

### 3. Monitoring Setup (Optional)

Consider integrating with monitoring services:
- **Prometheus + Grafana** for metrics
- **Sentry** for error tracking
- **Uptime monitoring** services

## Scaling

### Horizontal Scaling

For higher traffic, consider:

1. **Load Balancer**: Use Nginx or cloud load balancers
2. **Multiple Backend Instances**: Run multiple Gunicorn processes
3. **Database Scaling**: Read replicas, connection pooling
4. **CDN**: For static assets (CloudFlare, AWS CloudFront)

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Optimize database queries
- Enable database query caching
- Use Redis for session/cache storage

## Backup Strategy

### 1. Database Backup

```bash
# Create backup script
cat > /opt/rlcf/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/rlcf/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U rlcf_user rlcf_db > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# Compress and clean old backups (keep 30 days)
gzip "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: db_backup_$TIMESTAMP.sql.gz"
EOF

chmod +x /opt/rlcf/backup.sh
```

### 2. Automated Backups

```bash
# Add to crontab
sudo crontab -e
# Add line: 0 2 * * * /opt/rlcf/backup.sh
```

## Deployment Checklist

- [ ] Server provisioned and secured
- [ ] Database setup and configured
- [ ] SSL certificate installed
- [ ] Environment variables configured
- [ ] Backend service running and enabled
- [ ] Frontend built and served by Nginx
- [ ] Firewall configured
- [ ] Backup strategy implemented
- [ ] Monitoring setup
- [ ] Health checks passing
- [ ] DNS configured
- [ ] Performance testing completed

## Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   sudo systemctl status rlcf-backend
   sudo journalctl -u rlcf-backend --no-pager
   ```

2. **Database connection errors**:
   - Check PostgreSQL service status
   - Verify connection string in .env
   - Check firewall/security groups

3. **Frontend build errors**:
   ```bash
   cd /opt/rlcf/frontend
   npm run build 2>&1 | tee build.log
   ```

4. **SSL issues**:
   ```bash
   sudo certbot certificates
   sudo nginx -t
   ```

### Performance Optimization

1. **Database optimization**:
   ```sql
   -- Add indexes for frequently queried fields
   CREATE INDEX idx_tasks_status ON legal_tasks(status);
   CREATE INDEX idx_feedback_user_id ON feedback(user_id);
   ```

2. **Nginx optimization**:
   ```nginx
   # Add to server block
   gzip on;
   gzip_types text/plain text/css text/js application/javascript application/json;
   client_max_body_size 10M;
   ```

## Support

For deployment issues:
1. Check the logs first
2. Review this guide
3. Open an issue on GitHub
4. Contact the development team

---

## Quick Start Commands

```bash
# Complete deployment in one script
./deploy_production.sh

# Start services
sudo systemctl start rlcf-backend nginx

# Check status
sudo systemctl status rlcf-backend
curl https://your-domain.com/api/health

# View logs
sudo journalctl -u rlcf-backend -f
```

This deployment guide ensures a secure, scalable, and maintainable production environment for the RLCF Framework.