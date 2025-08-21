# Enhanced Dashboard Deployment Guide

This guide covers the deployment of the enhanced CredTech XScore dashboard with production-ready features including advanced monitoring, security, and performance optimizations.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Configuration Management](#configuration-management)
4. [Security Configuration](#security-configuration)
5. [Performance Optimization](#performance-optimization)
6. [Monitoring Setup](#monitoring-setup)
7. [Deployment Options](#deployment-options)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Health Checks](#health-checks)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended) or Windows Server 2019+
- **Python**: 3.8+ (3.9+ recommended)
- **Memory**: Minimum 4GB RAM, 8GB+ recommended
- **Storage**: Minimum 20GB free space
- **CPU**: 2+ cores recommended

### Software Dependencies

- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- Nginx (for production reverse proxy)
- SSL certificates (Let's Encrypt recommended)

### Python Dependencies

```bash
# Core requirements
pip install -r requirements.txt

# Additional production dependencies
pip install gunicorn uvicorn prometheus-client psutil
```

## Environment Setup

### 1. Clone and Setup Repository

```bash
git clone https://github.com/your-org/credtech-xscore.git
cd credtech-xscore

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root:

```bash
# Application Configuration
DASHBOARD_DEBUG_MODE=false
DASHBOARD_LOG_LEVEL=INFO
DASHBOARD_SESSION_TIMEOUT=24

# Security Configuration
SECURITY_JWT_SECRET=your-super-secret-jwt-key-here
SECURITY_SESSION_TIMEOUT=24
SECURITY_ENABLE_RATE_LIMITING=true
SECURITY_MAX_LOGIN_ATTEMPTS=5

# Performance Configuration
PERFORMANCE_CACHE_TTL=300
PERFORMANCE_ENABLE_CACHING=true
PERFORMANCE_MAX_CACHE_SIZE=1000

# Monitoring Configuration
MONITORING_ENABLE_METRICS=true
MONITORING_PROMETHEUS_PORT=8000
MONITORING_ENABLE_ALERTING=true

# Database Configuration (if applicable)
DATABASE_URL=postgresql://user:password@localhost:5432/credtech
DATABASE_POOL_SIZE=20

# External Services
REDIS_URL=redis://localhost:6379
API_BASE_URL=https://api.credtech.com
```

### 3. Directory Structure

Ensure the following directory structure exists:

```
credtech-xscore/
├── logs/
│   ├── app.log
│   ├── access.log
│   ├── error.log
│   ├── performance.log
│   └── security.log
├── data/
│   ├── dashboard/
│   ├── models/
│   └── cache/
├── config/
│   └── production/
└── scripts/
    └── deployment/
```

## Configuration Management

### 1. Dashboard Configuration

The dashboard uses a centralized configuration system. Key configuration files:

- `src/config/dashboard_config.py` - Main configuration classes
- `config/production/config.yaml` - Production-specific settings
- `.env` - Environment variables

### 2. Configuration Validation

Run configuration validation before deployment:

```bash
python -c "from src.config.dashboard_config import validate_config; print(validate_config())"
```

### 3. Configuration Updates

Update configurations programmatically:

```python
from src.config.dashboard_config import update_dashboard_config, update_security_config

# Update dashboard settings
update_dashboard_config(
    debug_mode=False,
    log_level="INFO",
    enable_monitoring=True
)

# Update security settings
update_security_config(
    enable_rate_limiting=True,
    max_login_attempts=5
)
```

## Security Configuration

### 1. Authentication & Authorization

```python
# Configure JWT settings
from src.config.dashboard_config import get_security_config

security_config = get_security_config()
security_config.jwt_secret_key = os.getenv('SECURITY_JWT_SECRET')
security_config.jwt_expiration_hours = 24
```

### 2. Rate Limiting

```python
# Configure rate limiting
from src.config.dashboard_config import get_security_config

security_config = get_security_config()
security_config.enable_rate_limiting = True
security_config.rate_limit_window_seconds = 60
security_config.rate_limit_max_requests = 60
```

### 3. Input Validation & Sanitization

```python
# Enable input validation
from src.config.dashboard_config import get_data_config

data_config = get_data_config()
data_config.enable_input_validation = True
data_config.enable_input_sanitization = True
data_config.max_input_length = 1000
```

### 4. Session Security

```python
# Configure session security
from src.config.dashboard_config import get_security_config

security_config = get_security_config()
security_config.enable_session_tracking = True
security_config.enable_ip_validation = True
security_config.enable_user_agent_validation = True
```

## Performance Optimization

### 1. Caching Configuration

```python
# Configure caching
from src.config.dashboard_config import get_performance_config

perf_config = get_performance_config()
perf_config.enable_lru_cache = True
perf_config.lru_cache_max_size = 1000
perf_config.enable_memory_cache = True
perf_config.memory_cache_ttl = 300
```

### 2. Connection Pooling

```python
# Configure database connections
from src.config.dashboard_config import get_performance_config

perf_config = get_performance_config()
perf_config.enable_connection_pooling = True
perf_config.max_database_connections = 20
perf_config.connection_timeout_seconds = 30
```

### 3. Async Processing

```python
# Configure async processing
from src.config.dashboard_config import get_performance_config

perf_config = get_performance_config()
perf_config.enable_async_processing = True
perf_config.max_worker_threads = 4
perf_config.task_queue_size = 100
```

## Monitoring Setup

### 1. Metrics Collection

```python
# Enable metrics collection
from src.config.dashboard_config import get_monitoring_config

monitoring_config = get_monitoring_config()
monitoring_config.enable_metrics_collection = True
monitoring_config.metrics_collection_interval = 60
```

### 2. Prometheus Integration

```python
# Configure Prometheus export
from src.config.dashboard_config import get_monitoring_config

monitoring_config = get_monitoring_config()
monitoring_config.enable_prometheus_export = True
monitoring_config.prometheus_port = 8000
```

### 3. Alerting Configuration

```python
# Configure alerting
from src.config.dashboard_config import get_monitoring_config

monitoring_config = get_monitoring_config()
monitoring_config.enable_email_alerts = True
monitoring_config.alert_email_recipients = ['admin@credtech.com']
monitoring_config.enable_slack_alerts = True
monitoring_config.slack_webhook_url = 'https://hooks.slack.com/...'
```

### 4. Health Checks

```python
# Configure health checks
from src.config.dashboard_config import get_monitoring_config

monitoring_config = get_monitoring_config()
monitoring_config.enable_health_checks = True
monitoring_config.health_check_interval = 30
monitoring_config.health_check_timeout = 10
```

## Deployment Options

### 1. Docker Deployment (Recommended)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DASHBOARD_DEBUG_MODE=false
      - SECURITY_JWT_SECRET=${SECURITY_JWT_SECRET}
      - MONITORING_ENABLE_METRICS=true
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./config:/app/config
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - dashboard
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

### 2. Systemd Service Deployment

Create `/etc/systemd/system/credtech-dashboard.service`:

```ini
[Unit]
Description=CredTech XScore Dashboard
After=network.target

[Service]
Type=simple
User=credtech
WorkingDirectory=/opt/credtech-xscore
Environment=PATH=/opt/credtech-xscore/venv/bin
ExecStart=/opt/credtech-xscore/venv/bin/streamlit run src/serve/app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Nginx Configuration

Create `/etc/nginx/sites-available/credtech-dashboard`:

```nginx
server {
    listen 80;
    server_name dashboard.credtech.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dashboard.credtech.com;

    ssl_certificate /etc/letsencrypt/live/dashboard.credtech.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.credtech.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=dashboard:10m rate=10r/s;
    limit_req zone=dashboard burst=20 nodelay;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

## CI/CD Pipeline

### 1. GitHub Actions Workflow

Create `.github/workflows/deploy-dashboard.yml`:

```yaml
name: Deploy Dashboard

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        # Add your deployment commands here
        echo "Deploying to production..."
```

### 2. Automated Testing

```bash
# Run all tests
pytest tests/ -v --cov=src --cov-report=html

# Run specific test categories
pytest tests/test_dashboard_enhancements.py -v
pytest tests/test_security_features.py -v
pytest tests/test_performance_features.py -v

# Run with performance profiling
pytest tests/ --durations=10 --durations-min=1.0
```

## Health Checks

### 1. Application Health Check

```python
# Health check endpoint
@app.route('/health')
def health_check():
    try:
        # Check database connectivity
        # Check external services
        # Check system resources
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'checks': {
                'database': 'ok',
                'cache': 'ok',
                'external_services': 'ok'
            }
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500
```

### 2. System Health Monitoring

```python
# System health check
def check_system_health():
    import psutil
    
    health_status = {
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'status': 'healthy'
    }
    
    # Check thresholds
    if (health_status['cpu_usage'] > 80 or 
        health_status['memory_usage'] > 85 or 
        health_status['disk_usage'] > 90):
        health_status['status'] = 'warning'
    
    return health_status
```

## Troubleshooting

### 1. Common Issues

#### Dashboard Not Loading
```bash
# Check logs
tail -f logs/app.log
tail -f logs/error.log

# Check process status
ps aux | grep streamlit
netstat -tlnp | grep 8501
```

#### Performance Issues
```bash
# Check system resources
htop
df -h
free -h

# Check application metrics
curl http://localhost:8000/metrics
```

#### Security Issues
```bash
# Check security logs
tail -f logs/security.log

# Check failed login attempts
grep "failed_login" logs/security.log
```

### 2. Debug Mode

Enable debug mode for troubleshooting:

```bash
export DASHBOARD_DEBUG_MODE=true
export DASHBOARD_LOG_LEVEL=DEBUG
```

### 3. Performance Profiling

```python
# Enable performance profiling
from src.utils.performance import track_performance

@track_performance("slow_operation")
def slow_function():
    # Your slow code here
    pass
```

### 4. Log Analysis

```bash
# Analyze error patterns
grep "ERROR" logs/app.log | cut -d' ' -f1 | sort | uniq -c | sort -nr

# Check user activity
grep "user_action" logs/app.log | jq '.user_id' | sort | uniq -c

# Monitor performance
grep "performance_metric" logs/performance.log | jq '.value' | awk '{sum+=$1} END {print sum/NR}'
```

## Maintenance

### 1. Regular Tasks

- **Daily**: Check error logs and alerts
- **Weekly**: Review performance metrics and optimize
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and update configurations

### 2. Backup Strategy

```bash
# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz config/

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# Backup data
tar -czf data-backup-$(date +%Y%m%d).tar.gz data/
```

### 3. Updates and Upgrades

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update configuration
git pull origin main
python -c "from src.config.dashboard_config import validate_config; print(validate_config())"

# Restart services
sudo systemctl restart credtech-dashboard
```

This deployment guide provides a comprehensive approach to deploying the enhanced CredTech XScore dashboard in a production environment with proper security, monitoring, and performance optimizations.

