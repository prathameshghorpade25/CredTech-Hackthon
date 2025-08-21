#!/bin/bash
# Script to check the health of the deployed application

set -e

# Default values
API_URL="http://localhost:8000/health"
TIMEOUT=5
RETRIES=3
INTERVAL=5

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --url|-u)
      API_URL="$2"
      shift 2
      ;;
    --timeout|-t)
      TIMEOUT="$2"
      shift 2
      ;;
    --retries|-r)
      RETRIES="$2"
      shift 2
      ;;
    --interval|-i)
      INTERVAL="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--url|-u <api_url>] [--timeout|-t <timeout>] [--retries|-r <retries>] [--interval|-i <interval>]"
      echo "  --url, -u: URL to check. Default: http://localhost:8000/health"
      echo "  --timeout, -t: Timeout in seconds. Default: 5"
      echo "  --retries, -r: Number of retries. Default: 3"
      echo "  --interval, -i: Interval between retries in seconds. Default: 5"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Checking health of API at $API_URL"
echo "Timeout: $TIMEOUT seconds"
echo "Retries: $RETRIES"
echo "Interval: $INTERVAL seconds"

for i in $(seq 1 $RETRIES); do
  echo "Attempt $i of $RETRIES..."
  
  # Use curl to check the health endpoint
  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -m $TIMEOUT $API_URL) || RESPONSE="FAILED"
  
  if [ "$RESPONSE" == "200" ]; then
    echo "Health check passed!"
    exit 0
  else
    echo "Health check failed with response: $RESPONSE"
    
    if [ $i -lt $RETRIES ]; then
      echo "Retrying in $INTERVAL seconds..."
      sleep $INTERVAL
    fi
  fi
done

echo "Health check failed after $RETRIES attempts"
exit 1