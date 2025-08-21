"""Script to run the FastAPI server for CredTech XScore API"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import security utilities
from src.utils.security import setup_https_config

# Load environment variables
load_dotenv()

# Get configuration from environment variables
HOST = os.getenv("API_HOST", "0.0.0.0")
PORT = int(os.getenv("API_PORT", "8000"))
RELOAD = os.getenv("API_RELOAD", "False").lower() == "true"
WORKERS = int(os.getenv("API_WORKERS", "1"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").lower()

def main():
    """Run the FastAPI server"""
    # Get HTTPS configuration
    https_config = setup_https_config()
    
    # Determine if we're using HTTPS
    using_https = bool(https_config)
    protocol = "https" if using_https else "http"
    
    print(f"Starting CredTech XScore API server on {protocol}://{HOST}:{PORT}")
    print(f"Documentation available at {protocol}://{HOST}:{PORT}/api/docs")
    print(f"HTTPS enabled: {using_https}")
    
    # Run the server with HTTPS if configured
    uvicorn.run(
        "src.serve.api:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        workers=WORKERS,
        log_level=LOG_LEVEL,
        **https_config
    )

if __name__ == "__main__":
    main()