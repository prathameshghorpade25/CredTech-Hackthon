"""Metrics endpoints for CredTech XScore API"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from src.utils.security import get_current_active_user
from src.utils.monitoring import get_current_metrics
from src.serve.api import User

# Create router
router = APIRouter()

@router.get("/api/metrics", tags=["monitoring"])
async def get_metrics(current_user: User = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Get current system and application metrics.
    
    This endpoint provides real-time metrics about the system and application,
    including CPU usage, memory usage, request counts, response times, and error rates.
    
    Authentication is required using a valid JWT token.
    
    Returns:
        Dict[str, Any]: A dictionary containing system and application metrics.
    """
    # Check if user has admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access metrics"
        )
    
    # Get current metrics
    metrics = get_current_metrics()
    
    return metrics

@router.get("/api/metrics/system", tags=["monitoring"])
async def get_system_metrics(current_user: User = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Get current system metrics.
    
    This endpoint provides real-time metrics about the system,
    including CPU usage, memory usage, and disk usage.
    
    Authentication is required using a valid JWT token.
    
    Returns:
        Dict[str, Any]: A dictionary containing system metrics.
    """
    # Check if user has admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access metrics"
        )
    
    # Get current metrics
    metrics = get_current_metrics()
    
    return metrics["system"]

@router.get("/api/metrics/application", tags=["monitoring"])
async def get_application_metrics(current_user: User = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Get current application metrics.
    
    This endpoint provides real-time metrics about the application,
    including request counts, response times, and error rates.
    
    Authentication is required using a valid JWT token.
    
    Returns:
        Dict[str, Any]: A dictionary containing application metrics.
    """
    # Check if user has admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access metrics"
        )
    
    # Get current metrics
    metrics = get_current_metrics()
    
    return metrics["application"]