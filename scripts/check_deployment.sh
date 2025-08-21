#!/bin/bash
# Script to check the deployment status of the application

set -e

# Default values
DEPLOYMENT_DIR="/opt/credtech-xscore"
HEALTH_CHECK_URL="http://localhost:8000/api/health"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dir|-d)
      DEPLOYMENT_DIR="$2"
      shift 2
      ;;
    --url|-u)
      HEALTH_CHECK_URL="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--dir|-d <deployment_directory>] [--url|-u <health_check_url>]"
      echo "  --dir, -d: Deployment directory. Default: /opt/credtech-xscore"
      echo "  --url, -u: Health check URL. Default: http://localhost:8000/api/health"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Checking deployment status"
echo "Deployment directory: $DEPLOYMENT_DIR"
echo "Health check URL: $HEALTH_CHECK_URL"

# Check if deployment directory exists
if [ ! -d "$DEPLOYMENT_DIR" ]; then
  echo "Error: Deployment directory does not exist"
  exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "$DEPLOYMENT_DIR/docker-compose.yml" ]; then
  echo "Error: docker-compose.yml not found in deployment directory"
  exit 1
fi

# Check if .env file exists
if [ ! -f "$DEPLOYMENT_DIR/.env" ]; then
  echo "Error: .env file not found in deployment directory"
  exit 1
fi

# Check container status
echo "\nChecking container status:"
cd "$DEPLOYMENT_DIR"
docker-compose ps

# Check container logs (last 10 lines)
echo "\nChecking container logs (last 10 lines):"
docker-compose logs --tail=10

# Check API health
echo "\nChecking API health:"
HEALTH_RESPONSE=$(curl -s "$HEALTH_CHECK_URL" || echo '{"status":"ERROR","message":"Failed to connect to API"}')

# Parse health response
STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d '"' -f 4)
MODEL_LOADED=$(echo "$HEALTH_RESPONSE" | grep -o '"model_loaded":[^,}]*' | cut -d ':' -f 2)

if [ "$STATUS" == "OK" ] || [ "$STATUS" == "ok" ]; then
  echo "API Status: OK"
  if [ "$MODEL_LOADED" == "true" ]; then
    echo "Model Status: Loaded"
    echo "Deployment is healthy!"
    exit 0
  else
    echo "Model Status: Not loaded"
    echo "Warning: API is running but model is not loaded"
    exit 2
  fi
else
  echo "API Status: $STATUS"
  echo "Error: API health check failed"
  exit 1
fi