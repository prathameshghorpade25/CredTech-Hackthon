from pathlib import Path
import pandas as pd
import joblib
import json
import os
import traceback
from typing import Optional, Dict, Any, Union

# Import the logger
from src.utils.logging import get_app_logger

# Create module logger
logger = get_app_logger(__name__)

def save_df(df: pd.DataFrame, path: str) -> bool:
    """
    Save DataFrame to CSV with error handling
    
    Args:
        df: DataFrame to save
        path: Path to save the DataFrame
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        logger.info(f"DataFrame saved successfully to {path}")
        return True
    except Exception as e:
        logger.error(f"Error saving DataFrame to {path}: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def load_df(path: str) -> Optional[pd.DataFrame]:
    """
    Load DataFrame from CSV with error handling
    
    Args:
        path: Path to load the DataFrame from
        
    Returns:
        DataFrame if successful, None otherwise
    """
    try:
        if not os.path.exists(path):
            logger.error(f"File not found: {path}")
            return None
            
        df = pd.read_csv(path)
        logger.info(f"DataFrame loaded successfully from {path}")
        return df
    except Exception as e:
        logger.error(f"Error loading DataFrame from {path}: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def save_json(obj: Dict[str, Any], path: str) -> bool:
    """
    Save object to JSON with error handling
    
    Args:
        obj: Object to save
        path: Path to save the object
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(obj, f, indent=2)
        logger.info(f"JSON saved successfully to {path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {path}: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def load_json(path: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON with error handling
    
    Args:
        path: Path to load the JSON from
        
    Returns:
        Dict if successful, None otherwise
    """
    try:
        if not os.path.exists(path):
            logger.error(f"File not found: {path}")
            return None
            
        with open(path, "r") as f:
            data = json.load(f)
        logger.info(f"JSON loaded successfully from {path}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON from {path}: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def save_model(model: Any, path: str) -> bool:
    """
    Save model with error handling
    
    Args:
        model: Model to save
        path: Path to save the model
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, path)
        logger.info(f"Model saved successfully to {path}")
        return True
    except Exception as e:
        logger.error(f"Error saving model to {path}: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def load_model(path: str) -> Optional[Any]:
    """
    Load model with error handling
    
    Args:
        path: Path to load the model from
        
    Returns:
        Model if successful, None otherwise
    """
    try:
        if not os.path.exists(path):
            logger.error(f"Model file not found: {path}")
            return None
            
        model = joblib.load(path)
        logger.info(f"Model loaded successfully from {path}")
        return model
    except Exception as e:
        logger.error(f"Error loading model from {path}: {str(e)}")
        logger.debug(traceback.format_exc())
        return None
