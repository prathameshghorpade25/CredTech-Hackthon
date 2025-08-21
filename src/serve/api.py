"""FastAPI implementation for CredTech XScore API"""

import os
import sys
import joblib
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exception_handlers import http_exception_handler
from src.utils.validation import BaseModel, Field, validator
from datetime import datetime, timedelta
import time
import traceback

# Import security utilities
from src.utils.security import (
    verify_password, get_password_hash, create_access_token,
    decode_access_token, encrypt_sensitive_data, decrypt_sensitive_data,
    setup_https_config
)

# Import monitoring utilities
from src.utils.monitoring import (
    start_monitoring, stop_monitoring, get_current_metrics,
    record_request, record_response_time, record_error
)
from src.utils.middleware import add_monitoring_middleware
from src.utils.prometheus_exporter import start_prometheus_server
from src.serve.metrics_endpoints import router as metrics_router
from src.serve.model_manager import model_manager

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.model.trainer import CreditScoreModel
from src.features.processor import FeatureProcessor
from src.utils.io import load_model
from src.utils.logging import get_app_logger
from src.utils.api_config import DATABASE_CONFIGS
from src.utils.validation import validate_credit_score_input, ValidationResult

# Set up logger
logger = get_app_logger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# JWT settings are now handled by the security module

# Initialize FastAPI app
app = FastAPI(
    title="CredTech XScore API",
    description="""API for credit scoring and financial data analysis.
    
    ## Features
    
    * **Credit Scoring**: Get credit scores for individuals or companies
    * **Batch Processing**: Score multiple profiles at once
    * **Model Information**: Access details about the credit scoring model
    * **Authentication**: Secure API access with JWT tokens
    
    ## Environment Variables
    
    The API requires several environment variables to be set:
    
    * `JWT_SECRET_KEY`: Secret key for JWT token generation
    * `JWT_ALGORITHM`: Algorithm used for JWT (default: HS256)
    * `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time in minutes
    
    For more information, see the .env.example file.
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=[
        {"name": "authentication", "description": "Operations related to user authentication and token generation"},
        {"name": "credit-scoring", "description": "Credit scoring endpoints for individual and batch processing"},
        {"name": "system", "description": "System health and information endpoints"},
        {"name": "data", "description": "Data retrieval endpoints for supporting information"},
        {"name": "monitoring", "description": "Monitoring and metrics endpoints for system and application performance"}
    ],
    contact={
        "name": "CredTech Support",
        "email": "support@credtech.example.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://credtech.example.com/license",
    }
)

# Add monitoring middleware
add_monitoring_middleware(app, logger=logger)

# Include metrics router
app.include_router(metrics_router)

# Custom middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = f"{time.time():.7f}"
    start_time = time.time()
    
    # Log request details
    logger.info(f"Request {request_id} started: {request.method} {request.url.path}")
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        
        # Log response details
        logger.info(f"Request {request_id} completed: {response.status_code} in {process_time:.4f}s")
        
        return response
    except Exception as e:
        # Log exception details
        logger.error(f"Request {request_id} failed: {str(e)}\n{traceback.format_exc()}")
        raise

# Custom exception handler for more detailed error responses
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return await http_exception_handler(request, exc)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),  # In production, set specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware for production
if os.getenv("ENVIRONMENT", "development") == "production":
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
    
    # In production, redirect HTTP to HTTPS
    app.add_middleware(HTTPSRedirectMiddleware)
    
    # Restrict hosts that can connect to your API
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost").split(",")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    # Only add HSTS header if using HTTPS
    if os.getenv("SSL_CERTFILE") and os.getenv("SSL_KEYFILE"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

# Pydantic models for request/response validation
class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type (always 'bearer')")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }

class TokenData(BaseModel):
    username: Optional[str] = Field(None, description="Username extracted from token")

class User(BaseModel):
    username: str = Field(..., description="Username for authentication")
    email: Optional[str] = Field(None, description="User email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    disabled: Optional[bool] = Field(None, description="Whether the user account is disabled")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "disabled": False
            }
        }

class UserInDB(User):
    hashed_password: str

class CreditScoreRequest(BaseModel):
    issuer: str = Field(..., description="Financial institution issuer code")
    income: float = Field(..., description="Annual income in dollars", gt=0)
    balance: float = Field(..., description="Current balance in dollars", ge=0)
    transactions: int = Field(..., description="Number of monthly transactions", ge=0)
    news_sentiment: float = Field(0.0, description="News sentiment score (-1 to 1)", ge=-1, le=1)
    
    class Config:
        schema_extra = {
            "example": {
                "issuer": "ABC",
                "income": 75000,
                "balance": 12000,
                "transactions": 15,
                "news_sentiment": 0.2
            }
        }

class BatchCreditScoreRequest(BaseModel):
    items: List[CreditScoreRequest] = Field(..., min_items=1, max_items=100)

class CreditScoreResponse(BaseModel):
    score: float = Field(..., description="Credit score (0-1000)")
    rating: str = Field(..., description="Credit rating (AAA to D)")
    risk_level: str = Field(..., description="Risk assessment")
    explanation: Dict[str, Any] = Field(..., description="Score explanation")
    timestamp: datetime = Field(default_factory=datetime.now)

class BatchCreditScoreResponse(BaseModel):
    results: List[CreditScoreResponse]
    count: int
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseModel):
    status: str = Field(..., description="API status (OK, Degraded, Error)")
    version: str = Field(..., description="API version")
    model_loaded: bool = Field(..., description="Whether the credit scoring model is loaded")
    timestamp: datetime = Field(default_factory=datetime.now, description="Current server timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "OK",
                "version": "1.0.0",
                "model_loaded": True,
                "timestamp": "2025-08-20T14:30:15.123456"
            }
        }

# Mock user database - in production, replace with real database
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@credtech.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        "disabled": False,
    }
}

def get_user(db, username: str):
    """Get user from database"""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(fake_db, username: str, password: str):
    """Authenticate a user with username and password"""
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except HTTPException:
        raise credentials_exception
    
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Model loading is now handled by the model_manager
def get_credit_model(model_id=None, request_id=None):
    """Get a model from the model manager
    
    Args:
        model_id: Optional specific model ID to use
        request_id: Optional request ID for A/B testing
        
    Returns:
        The loaded model or None if not available
    """
    try:
        model, _ = model_manager.get_model(model_id, request_id)
        return model
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None

# Map score to credit rating
def map_score_to_rating(score):
    """Map numerical score to letter rating"""
    if score >= 900:
        return "AAA", "Very Low Risk"
    elif score >= 800:
        return "AA", "Low Risk"
    elif score >= 700:
        return "A", "Low-Moderate Risk"
    elif score >= 600:
        return "BBB", "Moderate Risk"
    elif score >= 500:
        return "BB", "Moderate-High Risk"
    elif score >= 400:
        return "B", "High Risk"
    elif score >= 300:
        return "CCC", "Very High Risk"
    elif score >= 200:
        return "CC", "Extremely High Risk"
    elif score >= 100:
        return "C", "Near Default"
    else:
        return "D", "Default"

# API endpoints
@app.post("/api/token", response_model=Token, tags=["authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Generate JWT token for authentication.
    
    This endpoint authenticates a user and returns a JWT token that can be used
    for subsequent API calls. The token expires after a configurable amount of time.
    
    - **username**: Required for authentication
    - **password**: Required for authentication
    
    Returns a JWT token that should be included in the Authorization header
    of subsequent requests as a Bearer token.
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)  # Default to 30 minutes
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """API health check endpoint.
    
    This endpoint provides information about the API's health status,
    including whether the credit scoring model is loaded correctly.
    
    It can be used by monitoring systems to check if the API is functioning properly.
    
    No authentication is required for this endpoint.
    """
    model = get_credit_model()
    return {
        "status": "ok",
        "version": "1.0.0",
        "model_loaded": model is not None,
        "timestamp": datetime.now()
    }

@app.post("/api/score", response_model=CreditScoreResponse, tags=["credit-scoring"])
async def score_credit(
    request: CreditScoreRequest, 
    model_id: Optional[str] = Query(None, description="Specific model ID to use for scoring"),
    current_user: User = Depends(get_current_active_user)
):
    """Score a single credit profile.
    
    This endpoint calculates a credit score for a single issuer based on the provided financial data.
    
    The score is calculated using the trained machine learning model and includes:
    - A numerical score (0-1000)
    - A letter rating (AAA to D)
    - A risk level assessment
    - An explanation of the factors contributing to the score
    
    You can optionally specify a specific model ID to use for scoring.
    If not provided, the system will use A/B testing or the production model.
    
    Authentication is required using a valid JWT token.
    """
    # Generate a unique request ID for A/B testing and tracking
    request_id = str(time.time()) + "-" + request.issuer
    
    try:
        # Validate input data
        input_dict = {
            'issuer': request.issuer,
            'income': request.income,
            'balance': request.balance,
            'transactions': request.transactions,
            'news_sentiment': request.news_sentiment,
        }
        
        validation_result = validate_credit_score_input(input_dict)
        if not validation_result.is_valid:
            logger.warning(f"Validation failed for credit score request: {validation_result.errors}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Validation failed",
                    "errors": validation_result.errors
                }
            )
        
        # Prepare input data
        input_data = {
            'issuer': request.issuer,
            'asof_date': datetime.now().strftime('%Y-%m-%d'),
            'income': request.income,
            'balance': request.balance,
            'transactions': request.transactions,
            'news_sentiment_compound': request.news_sentiment,
            'news_sentiment_neg': max(0, -request.news_sentiment/2 + 0.5) if request.news_sentiment < 0 else 0,
            'news_sentiment_pos': max(0, request.news_sentiment/2 + 0.5) if request.news_sentiment > 0 else 0,
            'news_sentiment_neu': 1 - abs(request.news_sentiment),
        }
        
        # Create DataFrame
        input_df = pd.DataFrame([input_data])
        
        # Get prediction and explanation using model manager
        predictions, explanations, used_model_id = model_manager.predict_with_explanation(input_df, model_id, request_id)
        
        if len(predictions) == 0:
            raise HTTPException(status_code=503, detail="Model prediction failed")
            
        score_value = predictions[0] * 1000  # Scale to 0-1000 range
        
        # Map score to rating
        rating, risk_level = map_score_to_rating(score_value)
        
        # Create response
        response = {
            "score": float(score_value),
            "rating": rating,
            "risk_level": risk_level,
            "explanation": explanations[0] if explanations else {},
            "timestamp": datetime.now()
        }
        
        # Log the prediction
        logger.info(f"Credit score prediction: {score_value:.2f}, Rating: {rating}, Risk: {risk_level}, Model: {used_model_id}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in credit scoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/api/batch-score", response_model=BatchCreditScoreResponse, tags=["credit-scoring"])
async def batch_score_credit(
    request: BatchCreditScoreRequest, 
    model_id: Optional[str] = Query(None, description="Specific model ID to use for scoring"),
    current_user: User = Depends(get_current_active_user)
):
    """Score multiple credit profiles in batch.
    
    This endpoint allows scoring multiple issuers at once by providing a list of credit profiles.
    It's more efficient than making multiple individual scoring requests.
    
    The batch size is limited to 100 items per request to prevent overloading the system.
    
    Each item in the batch is validated individually, and any validation errors are returned
    with information about which items failed validation.
    
    You can optionally specify a specific model ID to use for scoring.
    If not provided, the system will use A/B testing or the production model.
    
    Authentication is required using a valid JWT token.
    """
    # Generate a unique request ID for A/B testing and tracking
    request_id = str(time.time()) + "-batch"
    
    try:
        results = []
        input_data_list = []
        validation_errors = []
        
        # Validate and prepare input data for each request
        for i, item in enumerate(request.items):
            # Validate input data
            input_dict = {
                'issuer': item.issuer,
                'income': item.income,
                'balance': item.balance,
                'transactions': item.transactions,
                'news_sentiment': item.news_sentiment,
            }
            
            validation_result = validate_credit_score_input(input_dict)
            if not validation_result.is_valid:
                validation_errors.append({
                    "index": i,
                    "errors": validation_result.errors
                })
                continue
            
            # Prepare input data
            input_data = {
                'issuer': item.issuer,
                'asof_date': datetime.now().strftime('%Y-%m-%d'),
                'income': item.income,
                'balance': item.balance,
                'transactions': item.transactions,
                'news_sentiment_compound': item.news_sentiment,
                'news_sentiment_neg': max(0, -item.news_sentiment/2 + 0.5) if item.news_sentiment < 0 else 0,
                'news_sentiment_pos': max(0, item.news_sentiment/2 + 0.5) if item.news_sentiment > 0 else 0,
                'news_sentiment_neu': 1 - abs(item.news_sentiment),
            }
            input_data_list.append(input_data)
        
        # If there are validation errors, return them
        if validation_errors:
            logger.warning(f"Validation failed for batch credit score request: {validation_errors}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Validation failed for some items",
                    "errors": validation_errors
                }
            )
        
        # If no valid items after validation, return error
        if not input_data_list:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No valid items to process"
            )
        
        # Create DataFrame
        input_df = pd.DataFrame(input_data_list)
        
        # Get batch predictions and explanations using model manager
        predictions, explanations, used_model_id = model_manager.predict_with_explanation(input_df, model_id, request_id)
        
        if len(predictions) == 0:
            raise HTTPException(status_code=503, detail="Model prediction failed")
        
        # Process each result
        for i, score in enumerate(predictions):
            score_value = score * 1000  # Scale to 0-1000 range
            rating, risk_level = map_score_to_rating(score_value)
            
            result = {
                "score": float(score_value),
                "rating": rating,
                "risk_level": risk_level,
                "explanation": explanations[i] if i < len(explanations) else {},
                "timestamp": datetime.now()
            }
            results.append(result)
        
        # Log the batch prediction
        logger.info(f"Batch credit score prediction completed for {len(results)} items using model {used_model_id}")
        
        return {
            "results": results,
            "count": len(results),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error in batch credit scoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing batch request: {str(e)}")

@app.get("/api/issuers", response_model=List[str], tags=["data"])
async def get_issuers(current_user: User = Depends(get_current_active_user)):
    """Get list of available issuers.
    
    This endpoint returns a list of issuers that can be used for credit scoring.
    The list includes financial institution issuer codes.
    
    In a production environment, this data would come from a database.
    Currently, it returns a predefined list of issuer codes.
    
    Authentication is required using a valid JWT token.
    """
    # In production, this would come from a database
    # Expanded list to include more issuers
    return ["ABC", "XYZ", "LMN", "QRS", "Apple Inc.", "Microsoft", "Amazon", "Google"]

@app.get("/api/model-info", tags=["system"])
async def get_model_info(
    model_id: Optional[str] = Query(None, description="Specific model ID to get info for"),
    current_user: User = Depends(get_current_active_user)
):
    """Get information about a model.
    
    This endpoint provides metadata about the machine learning model used for credit scoring,
    including its type, the features it uses, and when it was last trained.
    
    This information can be useful for understanding the model's capabilities and limitations,
    as well as for auditing and compliance purposes.
    
    You can optionally specify a specific model ID to get info for.
    If not provided, the system will return info for the production model.
    
    Authentication is required using a valid JWT token.
    """
    model_info = model_manager.get_model_info(model_id)
    
    if "error" in model_info:
        raise HTTPException(status_code=404, detail=model_info["error"])
    
    return model_info

# New endpoints for model versioning and A/B testing
@app.get("/api/models", tags=["system"])
async def list_models(current_user: User = Depends(get_current_active_user)):
    """List all available models.
    
    This endpoint returns a list of all models in the registry,
    including their IDs, versions, descriptions, and metrics.
    
    Authentication is required using a valid JWT token.
    """
    return model_manager.list_models()

@app.get("/api/experiments", tags=["system"])
async def list_experiments(current_user: User = Depends(get_current_active_user)):
    """List all A/B testing experiments.
    
    This endpoint returns a list of all experiments in the registry,
    including their IDs, descriptions, and model variants.
    
    Authentication is required using a valid JWT token.
    """
    return model_manager.list_experiments()

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("Starting CredTech XScore API")
    
    # Start monitoring with 60-second collection interval
    start_monitoring(collection_interval=60)
    
    # Start Prometheus metrics server on port 9090
    try:
        start_prometheus_server(port=9090)
        logger.info("Prometheus metrics server started")
    except Exception as e:
        logger.error(f"Failed to start Prometheus metrics server: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown"""
    logger.info("Shutting down CredTech XScore API")
    
    # Stop monitoring
    stop_monitoring()

# Run the application with uvicorn when this file is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)