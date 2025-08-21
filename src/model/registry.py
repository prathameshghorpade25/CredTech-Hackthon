"""Model registry for versioning and A/B testing"""

import os
import json
import shutil
import joblib
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

from src.utils.logging import get_app_logger

# Set up logger
logger = get_app_logger(__name__)

class ModelRegistry:
    """Registry for managing model versions and A/B testing"""
    
    def __init__(self, registry_dir: str = 'models/registry'):
        """Initialize the model registry
        
        Args:
            registry_dir: Directory to store model registry
        """
        self.registry_dir = registry_dir
        self.registry_file = os.path.join(registry_dir, 'registry.json')
        self.models_dir = os.path.join(registry_dir, 'models')
        
        # Create registry directory if it doesn't exist
        Path(self.registry_dir).mkdir(parents=True, exist_ok=True)
        Path(self.models_dir).mkdir(parents=True, exist_ok=True)
        
        # Load registry if it exists, otherwise create a new one
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                self.registry = json.load(f)
        else:
            self.registry = {
                "models": {},
                "production": None,
                "experiments": {},
                "default_traffic_split": {}
            }
            self._save_registry()
    
    def _save_registry(self):
        """Save registry to file"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def register_model(
        self, 
        model_path: str, 
        model_name: str,
        version: str,
        metrics: Dict[str, float],
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new model version
        
        Args:
            model_path: Path to the model file
            model_name: Name of the model
            version: Version of the model (e.g., '1.0.0')
            metrics: Dictionary of model metrics
            description: Description of the model
            metadata: Additional metadata
            
        Returns:
            model_id: Unique ID for the registered model
        """
        # Generate a unique ID for the model
        model_id = str(uuid.uuid4())
        
        # Create model directory
        model_dir = os.path.join(self.models_dir, model_id)
        Path(model_dir).mkdir(parents=True, exist_ok=True)
        
        # Copy model file to registry
        model_filename = os.path.basename(model_path)
        model_dest = os.path.join(model_dir, model_filename)
        shutil.copy(model_path, model_dest)
        
        # Create model metadata
        model_info = {
            "id": model_id,
            "name": model_name,
            "version": version,
            "metrics": metrics,
            "description": description,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "file_path": model_dest,
            "status": "registered"
        }
        
        # Add model to registry
        self.registry["models"][model_id] = model_info
        
        # Save registry
        self._save_registry()
        
        logger.info(f"Registered model {model_name} version {version} with ID {model_id}")
        
        return model_id
    
    def promote_to_production(self, model_id: str) -> bool:
        """Promote a model to production
        
        Args:
            model_id: ID of the model to promote
            
        Returns:
            success: Whether the promotion was successful
        """
        if model_id not in self.registry["models"]:
            logger.error(f"Model ID {model_id} not found in registry")
            return False
        
        # Update model status
        self.registry["models"][model_id]["status"] = "production"
        
        # Set as production model
        self.registry["production"] = model_id
        
        # Save registry
        self._save_registry()
        
        logger.info(f"Promoted model {model_id} to production")
        
        return True
    
    def get_production_model_id(self) -> Optional[str]:
        """Get the ID of the current production model
        
        Returns:
            model_id: ID of the production model, or None if no production model
        """
        return self.registry["production"]
    
    def load_model(self, model_id: Optional[str] = None) -> Any:
        """Load a model from the registry
        
        Args:
            model_id: ID of the model to load, or None to load production model
            
        Returns:
            model: The loaded model
        """
        if model_id is None:
            model_id = self.get_production_model_id()
            
        if model_id is None:
            logger.error("No production model available")
            return None
            
        if model_id not in self.registry["models"]:
            logger.error(f"Model ID {model_id} not found in registry")
            return None
        
        model_path = self.registry["models"][model_id]["file_path"]
        
        try:
            model = joblib.load(model_path)
            return model
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {str(e)}")
            return None
    
    def create_experiment(
        self, 
        name: str, 
        model_variants: Dict[str, float],
        description: str = ""
    ) -> str:
        """Create an A/B testing experiment
        
        Args:
            name: Name of the experiment
            model_variants: Dictionary mapping model IDs to traffic percentages
            description: Description of the experiment
            
        Returns:
            experiment_id: Unique ID for the experiment
        """
        # Validate model variants
        total_percentage = sum(model_variants.values())
        if not np.isclose(total_percentage, 100.0):
            logger.error(f"Total traffic percentage must be 100%, got {total_percentage}%")
            return ""
            
        for model_id in model_variants.keys():
            if model_id not in self.registry["models"]:
                logger.error(f"Model ID {model_id} not found in registry")
                return ""
        
        # Generate a unique ID for the experiment
        experiment_id = str(uuid.uuid4())
        
        # Create experiment metadata
        experiment_info = {
            "id": experiment_id,
            "name": name,
            "description": description,
            "model_variants": model_variants,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "results": {}
        }
        
        # Add experiment to registry
        self.registry["experiments"][experiment_id] = experiment_info
        
        # Update default traffic split
        self.registry["default_traffic_split"] = model_variants
        
        # Save registry
        self._save_registry()
        
        logger.info(f"Created experiment {name} with ID {experiment_id}")
        
        return experiment_id
    
    def get_model_for_request(self, request_id: str = None) -> str:
        """Get the model ID to use for a request based on traffic splitting
        
        Args:
            request_id: Unique identifier for the request, used for deterministic routing
            
        Returns:
            model_id: ID of the model to use
        """
        # If no active experiments, use production model
        if not self.registry["default_traffic_split"]:
            return self.get_production_model_id()
        
        # Use request_id for deterministic routing if provided
        if request_id:
            # Use hash of request_id to determine model
            hash_value = hash(request_id) % 100
        else:
            # Otherwise use random routing
            hash_value = np.random.randint(0, 100)
        
        # Get traffic split
        traffic_split = self.registry["default_traffic_split"]
        
        # Determine which model to use based on traffic percentages
        cumulative = 0
        for model_id, percentage in traffic_split.items():
            cumulative += percentage
            if hash_value < cumulative:
                return model_id
        
        # Fallback to production model
        return self.get_production_model_id()
    
    def record_prediction(
        self, 
        model_id: str, 
        request_data: Dict[str, Any],
        prediction: Any,
        actual: Any = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a prediction for model monitoring and A/B testing
        
        Args:
            model_id: ID of the model used for prediction
            request_data: Input data for the prediction
            prediction: Model prediction
            actual: Actual value (if available)
            metadata: Additional metadata
        """
        # Create prediction record
        record = {
            "model_id": model_id,
            "timestamp": datetime.now().isoformat(),
            "prediction": prediction,
            "actual": actual,
            "metadata": metadata or {}
        }
        
        # Store prediction record (in a real system, this would go to a database)
        # For simplicity, we'll just log it
        logger.debug(f"Recorded prediction for model {model_id}: {record}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all models in the registry
        
        Returns:
            models: List of model metadata
        """
        return list(self.registry["models"].values())
    
    def list_experiments(self) -> List[Dict[str, Any]]:
        """List all experiments in the registry
        
        Returns:
            experiments: List of experiment metadata
        """
        return list(self.registry["experiments"].values())
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a model
        
        Args:
            model_id: ID of the model
            
        Returns:
            model_info: Model metadata, or None if not found
        """
        return self.registry["models"].get(model_id)
    
    def get_experiment_info(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an experiment
        
        Args:
            experiment_id: ID of the experiment
            
        Returns:
            experiment_info: Experiment metadata, or None if not found
        """
        return self.registry["experiments"].get(experiment_id)