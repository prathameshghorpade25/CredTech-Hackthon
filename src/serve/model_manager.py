"""Model manager for API to handle model versioning and A/B testing"""

import os
import time
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import uuid

from src.model.registry import ModelRegistry
from src.utils.logging import get_app_logger
from src.utils.prometheus_exporter import record_model_prediction_latency, record_model_prediction_count

# Set up logger
logger = get_app_logger(__name__)

class ModelManager:
    """Manager for handling model versioning and A/B testing in the API"""
    
    def __init__(self):
        """Initialize the model manager"""
        self.registry = ModelRegistry()
        self.model_cache = {}
        self.last_refresh = 0
        self.cache_ttl = 300  # 5 minutes
    
    def get_model(self, model_id: Optional[str] = None, request_id: Optional[str] = None) -> Tuple[Any, str]:
        """Get a model from the registry with caching
        
        Args:
            model_id: Specific model ID to load, or None to use A/B testing or production model
            request_id: Request ID for deterministic A/B testing routing
            
        Returns:
            model: The loaded model
            model_id: ID of the model that was loaded
        """
        # If no specific model requested, use A/B testing or production model
        if model_id is None:
            model_id = self.registry.get_model_for_request(request_id)
        
        # If model is in cache and not expired, use it
        if model_id in self.model_cache and time.time() - self.last_refresh < self.cache_ttl:
            logger.debug(f"Using cached model {model_id}")
            return self.model_cache[model_id], model_id
        
        # Load model from registry
        logger.info(f"Loading model {model_id} from registry")
        model = self.registry.load_model(model_id)
        
        if model is None:
            # If model loading failed, try to load production model as fallback
            prod_id = self.registry.get_production_model_id()
            if prod_id is not None and prod_id != model_id:
                logger.warning(f"Failed to load model {model_id}, falling back to production model {prod_id}")
                model = self.registry.load_model(prod_id)
                model_id = prod_id
        
        # Update cache
        if model is not None:
            self.model_cache[model_id] = model
            self.last_refresh = time.time()
        
        return model, model_id
    
    def predict(self, data: pd.DataFrame, model_id: Optional[str] = None, request_id: Optional[str] = None) -> Tuple[np.ndarray, str]:
        """Make predictions using the specified model or A/B testing
        
        Args:
            data: Input data for prediction
            model_id: Specific model ID to use, or None to use A/B testing or production model
            request_id: Request ID for deterministic A/B testing routing
            
        Returns:
            predictions: Model predictions
            model_id: ID of the model that was used
        """
        # Generate request ID if not provided
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        # Get model
        start_time = time.time()
        model, model_id = self.get_model(model_id, request_id)
        
        if model is None:
            logger.error("No model available for prediction")
            return np.array([]), ""
        
        # Make prediction
        try:
            predictions = model.predict(data)
            
            # Record metrics
            latency = time.time() - start_time
            record_model_prediction_latency(model_id, latency)
            record_model_prediction_count(model_id, len(data))
            
            # Record prediction for A/B testing
            for i, row in data.iterrows():
                self.registry.record_prediction(
                    model_id=model_id,
                    request_data=row.to_dict(),
                    prediction=float(predictions[i]),
                    metadata={"request_id": request_id}
                )
            
            return predictions, model_id
        except Exception as e:
            logger.error(f"Error making prediction with model {model_id}: {str(e)}")
            return np.array([]), model_id
    
    def predict_with_explanation(self, data: pd.DataFrame, model_id: Optional[str] = None, request_id: Optional[str] = None) -> Tuple[np.ndarray, List[Dict[str, Any]], str]:
        """Make predictions with explanations
        
        Args:
            data: Input data for prediction
            model_id: Specific model ID to use, or None to use A/B testing or production model
            request_id: Request ID for deterministic A/B testing routing
            
        Returns:
            predictions: Model predictions
            explanations: List of explanations for each prediction
            model_id: ID of the model that was used
        """
        # Generate request ID if not provided
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        # Get model
        start_time = time.time()
        model, model_id = self.get_model(model_id, request_id)
        
        if model is None:
            logger.error("No model available for prediction")
            return np.array([]), [], ""
        
        # Make prediction with explanation
        try:
            predictions = model.predict(data)
            explanations = []
            
            # Generate explanation for each instance
            for i in range(len(data)):
                instance = data.iloc[[i]]
                explanation = model.explain_instance(instance)
                explanations.append(explanation)
            
            # Record metrics
            latency = time.time() - start_time
            record_model_prediction_latency(model_id, latency)
            record_model_prediction_count(model_id, len(data))
            
            # Record prediction for A/B testing
            for i, row in data.iterrows():
                self.registry.record_prediction(
                    model_id=model_id,
                    request_data=row.to_dict(),
                    prediction=float(predictions[i]),
                    metadata={"request_id": request_id}
                )
            
            return predictions, explanations, model_id
        except Exception as e:
            logger.error(f"Error making prediction with model {model_id}: {str(e)}")
            return np.array([]), [], model_id
    
    def get_model_info(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a model
        
        Args:
            model_id: ID of the model to get info for, or None for production model
            
        Returns:
            model_info: Information about the model
        """
        if model_id is None:
            model_id = self.registry.get_production_model_id()
        
        if model_id is None:
            return {
                "error": "No production model available"
            }
        
        model_info = self.registry.get_model_info(model_id)
        if model_info is None:
            return {
                "error": f"Model ID {model_id} not found"
            }
        
        # Format model info for API response
        return {
            "id": model_info["id"],
            "name": model_info["name"],
            "version": model_info["version"],
            "description": model_info["description"],
            "metrics": model_info["metrics"],
            "created_at": model_info["created_at"],
            "status": model_info["status"],
            "features": {
                "numerical": model_info["metadata"].get("numerical_features", []),
                "categorical": model_info["metadata"].get("categorical_features", [])
            },
            "is_production": model_info["id"] == self.registry.get_production_model_id()
        }
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all models in the registry
        
        Returns:
            models: List of model information
        """
        models = self.registry.list_models()
        production_id = self.registry.get_production_model_id()
        
        # Format model info for API response
        return [{
            "id": model["id"],
            "name": model["name"],
            "version": model["version"],
            "description": model["description"],
            "metrics": {
                "roc_auc": model["metrics"].get("roc_auc", 0.0),
                "pr_auc": model["metrics"].get("pr_auc", 0.0)
            },
            "created_at": model["created_at"],
            "status": model["status"],
            "is_production": model["id"] == production_id
        } for model in models]
    
    def list_experiments(self) -> List[Dict[str, Any]]:
        """List all experiments in the registry
        
        Returns:
            experiments: List of experiment information
        """
        experiments = self.registry.list_experiments()
        
        # Format experiment info for API response
        return [{
            "id": exp["id"],
            "name": exp["name"],
            "description": exp["description"],
            "model_variants": exp["model_variants"],
            "created_at": exp["created_at"],
            "status": exp["status"]
        } for exp in experiments]

# Singleton instance
model_manager = ModelManager()