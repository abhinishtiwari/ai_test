# Soulene Server - Deployment Guide

## 🚀 Deployment Options

### Option 1: Local Development

**Quick Start:**
```bash
# 1. Run setup
chmod +x setup.sh
./setup.sh

# 2. Start server
chmod +x run_server.sh
./run_server.sh

# 3. Open chat_interface.html in browser
```

**Manual Setup:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run server
python soulene_server.py
```

---

### Option 2: Docker Deployment

**Prerequisites:**
- Docker installed
- Docker Compose installed

**Steps:**

1. **Build the image:**
```bash
docker build -t soulene-server .
```

2. **Run with Docker Compose:**
```bash
# Make sure .env file exists with your API key
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

3. **Or run directly with Docker:**
```bash
docker run -d \
  --name soulene \
  -p 5000:5000 \
  -e GOOGLE_API_KEY=your_api_key_here \
  --restart unless-stopped \
  soulene-server
```

---

### Option 3: Production Server (Ubuntu/Debian)

**1. System Setup:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Nginx (optional, for reverse proxy)
sudo apt install nginx -y
```

**2. Application Setup:**
```bash
# Create application directory
sudo mkdir -p /opt/soulene
cd /opt/soulene

# Copy files (use git clone or scp)
# git clone <your-repo> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
sudo nano .env
# Add GOOGLE_API_KEY and other settings
```

**3. Create Systemd Service:**

Create `/etc/systemd/system/soulene.service`:

```ini
[Unit]
Description=Soulene Mental Health Support Server
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/soulene
Environment="PATH=/opt/soulene/venv/bin"
EnvironmentFile=/opt/soulene/.env
ExecStart=/opt/soulene/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile /var/log/soulene/access.log \
    --error-logfile /var/log/soulene/error.log \
    soulene_server:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**4. Setup Logging:**
```bash
sudo mkdir -p /var/log/soulene
sudo chown www-data:www-data /var/log/soulene
```

**5. Start Service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable soulene
sudo systemctl start soulene
sudo systemctl status soulene
```

**6. Configure Nginx (Optional):**

Create `/etc/nginx/sites-available/soulene`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location / {
        root /opt/soulene;
        try_files $uri $uri/ =404;
    }

    # API proxy
    location /chat {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
    }
}
```

Enable and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/soulene /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**7. Setup SSL (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

### Option 4: Cloud Deployment

#### AWS EC2

1. **Launch EC2 Instance:**
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t3.small or larger
   - Security group: Allow ports 22, 80, 443

2. **Connect and setup:**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip

# Follow "Production Server" steps above
```

3. **Configure AWS Secrets Manager (optional):**
```bash
pip install boto3

# Modify soulene_server.py to fetch API key from Secrets Manager
```

#### Google Cloud Platform

1. **Create VM Instance:**
```bash
gcloud compute instances create soulene-server \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=e2-small \
    --zone=us-central1-a
```

2. **SSH and setup:**
```bash
gcloud compute ssh soulene-server

# Follow "Production Server" steps above
```

#### Heroku

1. **Create Procfile:**
```
web: gunicorn soulene_server:app
```

2. **Deploy:**
```bash
heroku create your-app-name
heroku config:set GOOGLE_API_KEY=your_key_here
git push heroku main
```

#### DigitalOcean

1. **Create Droplet:**
   - Ubuntu 22.04
   - Basic plan ($6/month minimum)

2. **Setup:**
```bash
ssh root@your-droplet-ip

# Follow "Production Server" steps above
```

---

## 🔒 Security Hardening

### 1. Remove Hardcoded API Key

**CRITICAL - Before ANY deployment:**

Edit `soulene_server.py`:

```python
# REMOVE THIS:
API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyDCnHKDc49Qfxh1expBsB-S_CIUvCBBQ3Y')

# REPLACE WITH:
API_KEY = os.getenv('GOOGLE_API_KEY')
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable must be set")
```

### 2. Add Rate Limiting

```bash
pip install Flask-Limiter
```

Add to `soulene_server.py`:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=self.app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "10 per minute"],
    storage_uri="memory://"
)

# Apply to chat endpoint
@limiter.limit("30 per hour")
@self.app.route('/chat', methods=['POST'])
def chat():
    # ... existing code
```

### 3. Restrict CORS

```python
# In production, replace:
CORS(app, resources={r"/*": {"origins": "*"}})

# With:
CORS(app, resources={
    r"/*": {
        "origins": ["https://your-domain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

### 4. Add Input Validation

```python
from werkzeug.utils import escape

def validate_message(message):
    if not message or not isinstance(message, str):
        raise ValueError("Invalid message")
    
    # Sanitize
    message = escape(message)
    
    # Length limit
    if len(message) > 5000:
        raise ValueError("Message too long")
    
    return message.strip()
```

### 5. Implement Session Authentication (Optional)

```python
import secrets
from functools import wraps

# Generate session tokens
SESSION_TOKENS = {}

def require_session(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Session-Token')
        if not token or token not in SESSION_TOKENS:
            return jsonify({"error": "Invalid session"}), 401
        return f(*args, **kwargs)
    return decorated
```

### 6. Enable HTTPS Only

In production, always use HTTPS. Update Nginx config:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # ... rest of config
}
```

---

## 📊 Monitoring & Logging

### Setup Application Logging

Add to `soulene_server.py`:

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
handler = RotatingFileHandler(
    'soulene.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
```

### Monitor with systemd

```bash
# View logs
sudo journalctl -u soulene -f

# Check status
sudo systemctl status soulene

# Restart service
sudo systemctl restart soulene
```

### Setup Monitoring (Optional)

**Prometheus + Grafana:**

```bash
pip install prometheus-flask-exporter
```

Add to server:

```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(self.app)
```

---

## 🧪 Testing Deployment

### 1. Health Check
```bash
curl https://your-domain.com/health
```

### 2. Chat Endpoint
```bash
curl -X POST https://your-domain.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### 3. Load Testing
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test 1000 requests, 10 concurrent
ab -n 1000 -c 10 -p test_payload.json \
   -T application/json \
   https://your-domain.com/chat
```

### 4. Security Scan
```bash
# Install nikto
sudo apt install nikto

# Scan for vulnerabilities
nikto -h https://your-domain.com
```

---

## 🔧 Troubleshooting

### Server won't start
```bash
# Check logs
sudo journalctl -u soulene -n 50

# Check permissions
ls -la /opt/soulene

# Verify API key
grep GOOGLE_API_KEY /opt/soulene/.env
```

### High memory usage
```bash
# Monitor resources
htop

# Reduce workers in gunicorn
# Edit service file: --workers 2 instead of 4

# Restart
sudo systemctl restart soulene
```

### Slow responses
```bash
# Check network latency
ping api.anthropic.com

# Monitor API calls
tail -f /var/log/soulene/access.log

# Consider caching responses
pip install flask-caching
```

---

## 📈 Scaling Considerations

### Horizontal Scaling

Use load balancer (Nginx/HAProxy) with multiple instances:

```nginx
upstream soulene_backend {
    least_conn;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    location /chat {
        proxy_pass http://soulene_backend;
    }
}
```

### Database Integration

For persistent sessions:

```bash
pip install redis flask-session
```

```python
from flask_session import Session
import redis

# Configure Redis session storage
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
Session(app)
```

---

## ✅ Pre-Deployment Checklist

- [ ] Remove hardcoded API key
- [ ] Set all environment variables
- [ ] Configure CORS for production domain
- [ ] Enable HTTPS/SSL
- [ ] Add rate limiting
- [ ] Setup logging
- [ ] Configure firewall (ufw/iptables)
- [ ] Test all endpoints
- [ ] Setup monitoring
- [ ] Create backup strategy
- [ ] Document emergency procedures
- [ ] Review security headers
- [ ] Test error handling
- [ ] Verify health checks
- [ ] Setup auto-restart on failure

---

## 📞 Support

For deployment issues:
- Check logs first
- Review this guide
- Test with curl/Postman
- Contact your cloud provider support

**Emergency Shutdown:**
```bash
sudo systemctl stop soulene
```

---

**Remember**: This is a mental health support application. Ensure high availability and have emergency procedures in place!
