# CredTech XScore Production Deployment Guide

## Overview

This guide provides instructions for deploying the CredTech XScore API to production environments. The deployment process is automated through a CI/CD pipeline using GitHub Actions, with support for both staging and production environments.

## Prerequisites

- Docker and Docker Compose installed on the target server
- SSH access to the target server
- GitHub repository access with appropriate permissions
- SSL certificates for HTTPS (recommended for production)

## Deployment Architecture

The CredTech XScore application is deployed as a set of Docker containers:

- **API Service**: FastAPI application serving the credit scoring API
- **Pipeline Service**: Data processing pipeline for credit scoring
- **Streamlit Service**: Web interface for interacting with the API

## Deployment Environments

### Staging Environment

The staging environment is automatically deployed when changes are pushed to the `develop` branch. It is intended for testing and validation before production deployment.

### Production Environment

The production environment is deployed when a new version tag (e.g., `v1.0.0`) is pushed to the repository. It is the live environment used by clients.

## CI/CD Pipeline

The CI/CD pipeline is implemented using GitHub Actions and consists of the following stages:

1. **Test**: Run unit tests, linting, and code quality checks
2. **Build and Push**: Build Docker images and push them to GitHub Container Registry
3. **Deploy to Staging**: Deploy to the staging environment (for `develop` branch)
4. **Deploy to Production**: Deploy to the production environment (for version tags)

## Manual Deployment

If you need to deploy manually, follow these steps:

### 1. Prepare the Deployment Environment

```bash
# Clone the repository
git clone https://github.com/your-org/credtech-xscore.git
cd credtech-xscore

# Prepare the deployment environment
bash scripts/prepare_deployment.sh --environment production --dir /opt/credtech-xscore
```

### 2. Configure Environment Variables

Create a `.env` file in the deployment directory with the following variables:

```
# API Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENCRYPTION_KEY=your-encryption-key
CORS_ORIGINS=["https://api.credtech.com","https://app.credtech.com"]
ALLOWED_HOSTS=["api.credtech.com"]

# SSL Configuration (if using HTTPS)
SSL_KEYFILE=/path/to/keyfile
SSL_CERTFILE=/path/to/certfile

# Monitoring
PROMETHEUS_PORT=9090
METRICS_COLLECTION_INTERVAL=60
CPU_ALERT_THRESHOLD=80
MEMORY_ALERT_THRESHOLD=80
DISK_ALERT_THRESHOLD=85
ERROR_RATE_THRESHOLD=5
RESPONSE_TIME_THRESHOLD=2000

# Docker Registry
REGISTRY=ghcr.io
IMAGE_NAME=your-org/credtech-xscore
IMAGE_TAG=latest
```

### 3. Deploy the Application

```bash
bash scripts/deploy.sh --environment production --dir /opt/credtech-xscore --tag v1.0.0
```

### 4. Verify the Deployment

```bash
bash scripts/check_deployment.sh --dir /opt/credtech-xscore --url https://api.credtech.com/api/health
```

## Rollback Procedure

If you need to rollback to a previous version, use the rollback script:

```bash
bash scripts/rollback.sh --dir /opt/credtech-xscore --tag v0.9.0
```

## Health Monitoring

The application provides a health check endpoint at `/api/health` that can be used to monitor the health of the API. You can use the `health_check.sh` script to check the health of the API:

```bash
bash scripts/health_check.sh --url https://api.credtech.com/api/health
```

## Scaling

To scale the application, you can adjust the following parameters:

- **API_WORKERS**: Number of worker processes for the API service
- **Docker Compose scale**: Use `docker-compose up -d --scale api=3` to run multiple instances of the API service

## Backup and Restore

### Backup

1. Back up the `.env` file and any other configuration files
2. Back up the database (if applicable)

### Restore

1. Restore the `.env` file and any other configuration files
2. Restore the database (if applicable)
3. Deploy the application using the deploy script

## Security Considerations

- Use HTTPS in production (configure SSL_KEYFILE and SSL_CERTFILE)
- Set strong JWT_SECRET_KEY and ENCRYPTION_KEY values
- Restrict CORS_ORIGINS and ALLOWED_HOSTS to trusted domains
- Use a firewall to restrict access to the server
- Set up monitoring and alerting for security events

## Troubleshooting

### Common Issues

1. **API not responding**
   - Check if containers are running: `docker-compose ps`
   - Check container logs: `docker-compose logs api`
   - Verify health check: `bash scripts/health_check.sh`

2. **Authentication failures**
   - Check JWT_SECRET_KEY and JWT_ALGORITHM settings
   - Verify token expiration time (ACCESS_TOKEN_EXPIRE_MINUTES)

3. **Database connection issues**
   - Check database connection settings
   - Verify database is running and accessible

### Getting Help

If you encounter issues that you cannot resolve, contact the development team at support@credtech.example.com.

## Maintenance

### Regular Updates

1. Pull the latest changes from the repository
2. Run the deployment script with the new version tag

### Monitoring and Logging

- Access logs are available in the container logs
- Metrics are available at `/api/metrics` (requires admin authentication)
- Prometheus metrics are exposed on port 9090

## Conclusion

This guide provides the basic steps for deploying the CredTech XScore API to production. For more detailed information, refer to the API documentation and the source code repository.