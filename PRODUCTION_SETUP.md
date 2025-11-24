# French Word List - Production Setup Guide

## Overview
This guide provides step-by-step instructions to deploy your French Word List Flask application to production. The app is currently using CSV files for data storage, which works well for this use case.

## Prerequisites
- Python 3.12+
- Git
- A cloud hosting service account (Heroku, DigitalOcean, AWS, etc.)

## 1. Environment Setup

### Create Production Environment File
```bash
cp .env.example .env
```

Edit `.env` with your production values:
```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

Update `.env`:
```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-generated-secure-key-here
APP_NAME=French Words Collection
```

## 2. Install Production Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install production dependencies
pip install -r requirements.txt
```

## 3. Test Production Configuration

```bash
# Test with production settings
export FLASK_ENV=production
export FLASK_DEBUG=False
python wsgi.py
```

## 4. Deployment Options

### Option A: Heroku (Recommended for Beginners)

#### 1. Install Heroku CLI
```bash
# macOS with Homebrew
brew install heroku/brew/heroku

# Or download from https://devcenter.heroku.com/articles/heroku-cli
```

#### 2. Login and Create App
```bash
heroku login
heroku create your-app-name
```

#### 3. Configure Environment Variables
```bash
heroku config:set FLASK_ENV=production
heroku config:set FLASK_DEBUG=False
heroku config:set SECRET_KEY=your-secure-secret-key
```

#### 4. Deploy
```bash
git add .
git commit -m "Prepare for production deployment"
git push heroku main
```

#### 5. Open Your App
```bash
heroku open
```

### Option B: DigitalOcean App Platform

#### 1. Create App Spec (app.yaml)
```yaml
name: french-words-app
services:
- name: web
  source_dir: /
  github:
    repo: your-username/french-word-list
    branch: main
  run_command: gunicorn --worker-tmp-dir /dev/shm wsgi:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: FLASK_ENV
    value: production
  - key: FLASK_DEBUG
    value: "False"
  - key: SECRET_KEY
    value: your-secure-secret-key
```

#### 2. Deploy via DigitalOcean Dashboard
- Go to https://cloud.digitalocean.com/apps
- Create new app from GitHub repository
- Use the app.yaml configuration

### Option C: AWS Elastic Beanstalk

#### 1. Install AWS CLI
```bash
# macOS
brew install awscli

# Configure AWS credentials
aws configure
```

#### 2. Initialize EB Application
```bash
pip install awsebcli
eb init
```

#### 3. Create Environment
```bash
eb create production-env
```

#### 4. Set Environment Variables
```bash
eb setenv FLASK_ENV=production FLASK_DEBUG=False SECRET_KEY=your-key
```

#### 5. Deploy
```bash
eb deploy
```

### Option D: Manual VPS/Server Setup

#### 1. Server Setup (Ubuntu/Debian)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install nginx
sudo apt install nginx -y

# Install certbot for SSL (optional)
sudo apt install certbot python3-certbot-nginx -y
```

#### 2. Application Setup
```bash
# Clone your repository
git clone https://github.com/your-username/french-word-list.git
cd french-word-list

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

#### 3. Create Systemd Service
Create `/etc/systemd/system/french-words.service`:
```ini
[Unit]
Description=French Words Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/app
Environment="PATH=/path/to/your/app/venv/bin"
Environment="FLASK_ENV=production"
Environment="FLASK_DEBUG=False"
Environment="SECRET_KEY=your-secure-key"
ExecStart=/path/to/your/app/venv/bin/gunicorn --workers 3 --bind unix:french-words.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

#### 4. Configure Nginx
Create `/etc/nginx/sites-available/french-words`:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/your/app/french-words.sock;
    }
}
```

#### 5. Enable and Start Services
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/french-words /etc/nginx/sites-enabled

# Test nginx configuration
sudo nginx -t

# Start services
sudo systemctl start french-words
sudo systemctl enable french-words
sudo systemctl restart nginx
```

## 5. SSL Certificate (HTTPS)

### Using Certbot (Let's Encrypt)
```bash
# For nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Automatic renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 6. Database Migration (Future Enhancement)

When you want to move from CSV to a database:

### Option 1: SQLite (Simple)
```python
# In viewer.py
import sqlite3
from flask import g

DATABASE = 'words.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
```

### Option 2: PostgreSQL (Production Ready)
```bash
pip install psycopg2-binary
```

Update your `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/french_words
```

## 7. Monitoring and Maintenance

### Basic Monitoring
```bash
# Check app status
sudo systemctl status french-words

# View logs
sudo journalctl -u french-words -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Backup Strategy
```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_$DATE.tar.gz words_good.csv words_missing.csv
```

### Performance Optimization
- Enable gzip compression in nginx
- Set up caching headers for static assets
- Consider using a CDN for static files
- Monitor memory usage and adjust worker count

## 8. Security Checklist

- [ ] Changed default SECRET_KEY
- [ ] Set FLASK_ENV=production
- [ ] Disabled FLASK_DEBUG
- [ ] HTTPS enabled
- [ ] Regular security updates
- [ ] Firewall configured
- [ ] File permissions set correctly (755 for directories, 644 for files)
- [ ] Database credentials secured
- [ ] Sensitive files in .gitignore

## 9. Troubleshooting

### Common Issues

**App not starting:**
```bash
# Check logs
sudo journalctl -u french-words -n 50

# Test gunicorn directly
cd /path/to/app
source venv/bin/activate
gunicorn wsgi:app
```

**Permission errors:**
```bash
# Fix permissions
sudo chown -R www-data:www-data /path/to/app
sudo chmod -R 755 /path/to/app
```

**Port conflicts:**
```bash
# Check what's using port 80/443
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443
```

## 10. Cost Comparison

| Platform | Free Tier | Paid Plans | Best For |
|----------|-----------|------------|----------|
| Heroku | 550-1000 hours/month | $7+/month | Quick deployment |
| DigitalOcean | No | $5+/month | VPS control |
| AWS EB | 750 hours/month | $10+/month | Enterprise |
| VPS | No | $5+/month | Full control |

## 11. Next Steps

1. Set up monitoring (UptimeRobot, Pingdom)
2. Configure backups
3. Set up CI/CD pipeline
4. Add error tracking (Sentry)
5. Implement caching (Redis)
6. Add analytics (Google Analytics)

## Support

If you encounter issues:
1. Check the application logs
2. Verify environment variables
3. Test locally with production settings
4. Check file permissions
5. Review nginx configuration

Remember to regularly update dependencies and monitor your application performance!