#!/bin/bash
# Script to prepare environment for deployment

set -e

# Default values
ENVIRONMENT="staging"
DEPLOYMENT_DIR="/opt/credtech-xscore"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --environment|-e)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --dir|-d)
      DEPLOYMENT_DIR="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--environment|-e <environment>] [--dir|-d <deployment_directory>]"
      echo "  --environment, -e: Environment to deploy to (staging or production). Default: staging"
      echo "  --dir, -d: Directory to deploy to. Default: /opt/credtech-xscore"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Preparing deployment environment: $ENVIRONMENT"
echo "Deployment directory: $DEPLOYMENT_DIR"

# Create deployment directory if it doesn't exist
mkdir -p "$DEPLOYMENT_DIR"

# Copy docker-compose.yml to deployment directory
cp docker-compose.yml "$DEPLOYMENT_DIR/"

# Create environment-specific .env file
if [ "$ENVIRONMENT" == "production" ]; then
  echo "Creating production environment configuration"
  cat > "$DEPLOYMENT_DIR/.env.deployment" << EOF
ENVIRONMENT=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
PROMETHEUS_PORT=9090
METRICS_COLLECTION_INTERVAL=60
CPU_ALERT_THRESHOLD=80
MEMORY_ALERT_THRESHOLD=80
DISK_ALERT_THRESHOLD=85
ERROR_RATE_THRESHOLD=5
RESPONSE_TIME_THRESHOLD=2000
CORS_ORIGINS=["https://api.credtech.com","https://app.credtech.com"]
ALLOWED_HOSTS=["api.credtech.com"]
EOF
else
  echo "Creating staging environment configuration"
  cat > "$DEPLOYMENT_DIR/.env.deployment" << EOF
ENVIRONMENT=staging
LOG_LEVEL=DEBUG
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=2
PROMETHEUS_PORT=9090
METRICS_COLLECTION_INTERVAL=30
CPU_ALERT_THRESHOLD=70
MEMORY_ALERT_THRESHOLD=70
DISK_ALERT_THRESHOLD=75
ERROR_RATE_THRESHOLD=10
RESPONSE_TIME_THRESHOLD=3000
CORS_ORIGINS=["https://staging-api.credtech.com","https://staging-app.credtech.com","http://localhost:3000"]
ALLOWED_HOSTS=["staging-api.credtech.com","localhost"]
EOF
fi

echo "Deployment environment prepared successfully"