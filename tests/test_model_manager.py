import os
import pytest
import tempfile
import shutil
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.model.registry import ModelRegistry
from src.serve.model_manager import ModelManager


@pytest.fixture
def temp_registry_dir():
    """Create a temporary directory for the model registry."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_registry(temp_registry_dir):
    """Create a mock model registry."""
    registry = ModelRegistry(registry_dir=temp_registry_dir)
    return registry


@pytest.fixture
def mock_model():
    """Create a mock model for testing."""
    model = MagicMock()
    model.predict.return_value = np.array([0.2, 0.8, 0.5])
    model.predict_with_explanation.return_value = {
        "scores": np.array([0.2, 0.8, 0.5]),
        "explanations": [
            {"feature1": 0.1, "feature2": -0.2},
            {"feature1": -0.3, "feature2": 0.4},
            {"feature1": 0.2, "feature2": 0.1}
        ]
    }
    return model


@pytest.fixture
def model_manager(mock_registry):
    """Create a model manager instance with a mock registry."""
    with patch("src.serve.model_manager.ModelRegistry", return_value=mock_registry):
        manager = ModelManager()
        manager.registry = mock_registry
        yield manager


def test_get_model_production(model_manager, mock_registry, mock_model):
    """Test getting the production model."""
    # Mock the registry to return a production model ID
    mock_registry.get_production_model_id.return_value = "model_123"
    mock_registry.load_model.return_value = mock_model
    
    # Get the model
    model = model_manager.get_model()
    
    # Check that the correct model was returned
    assert model == mock_model
    mock_registry.get_production_model_id.assert_called_once()
    mock_registry.load_model.assert_called_once_with("model_123")


def test_get_model_specific_id(model_manager, mock_registry, mock_model):
    """Test getting a specific model by ID."""
    # Mock the registry to return a model
    mock_registry.load_model.return_value = mock_model
    
    # Get the model
    model = model_manager.get_model(model_id="model_456")
    
    # Check that the correct model was returned
    assert model == mock_model
    mock_registry.load_model.assert_called_once_with("model_456")


def test_get_model_ab_testing(model_manager, mock_registry, mock_model):
    """Test getting a model with A/B testing."""
    # Mock the registry to return an active experiment
    experiment = {
        "id": "exp_123",
        "name": "Test Experiment",
        "model_ids": ["model_123", "model_456"],
        "traffic_split": [70, 30],
        "status": "active"
    }
    mock_registry.get_active_experiment.return_value = experiment
    mock_registry.load_model.return_value = mock_model
    
    # Get the model with a request ID that should route to the first model
    with patch("src.serve.model_manager.hash_request_id", return_value=30):
        model, model_id = model_manager.get_model(request_id="req_123")
    
    # Check that the correct model was returned
    assert model == mock_model
    assert model_id == "model_123"
    mock_registry.load_model.assert_called_once_with("model_123")


def test_predict(model_manager, mock_registry, mock_model):
    """Test making predictions with the model manager."""
    # Mock the registry and model
    mock_registry.get_production_model_id.return_value = "model_123"
    mock_registry.load_model.return_value = mock_model
    
    # Make a prediction
    features = pd.DataFrame({
        "feature1": [1, 2, 3],
        "feature2": [4, 5, 6]
    })
    scores = model_manager.predict(features)
    
    # Check that the correct scores were returned
    np.testing.assert_array_equal(scores, np.array([0.2, 0.8, 0.5]))
    mock_model.predict.assert_called_once()


def test_predict_with_explanation(model_manager, mock_registry, mock_model):
    """Test making predictions with explanations."""
    # Mock the registry and model
    mock_registry.get_production_model_id.return_value = "model_123"
    mock_registry.load_model.return_value = mock_model
    
    # Make a prediction with explanation
    features = pd.DataFrame({
        "feature1": [1, 2, 3],
        "feature2": [4, 5, 6]
    })
    result = model_manager.predict_with_explanation(features)
    
    # Check that the correct result was returned
    assert "scores" in result
    assert "explanations" in result
    np.testing.assert_array_equal(result["scores"], np.array([0.2, 0.8, 0.5]))
    assert len(result["explanations"]) == 3
    mock_model.predict_with_explanation.assert_called_once()


def test_get_model_info(model_manager, mock_registry):
    """Test getting model information."""
    # Mock the registry to return model metadata
    metadata = {
        "id": "model_123",
        "version": "v1.0.0",
        "description": "Test model",
        "feature_names": ["feature1", "feature2"],
        "model_type": "lightgbm",
        "training_date": "2023-01-01T12:00:00",
        "metrics": {
            "roc_auc": 0.85,
            "pr_auc": 0.75
        }
    }
    mock_registry.get_production_model_id.return_value = "model_123"
    mock_registry.get_model_metadata.return_value = metadata
    
    # Get model info
    info = model_manager.get_model_info()
    
    # Check that the correct info was returned
    assert info == metadata
    mock_registry.get_production_model_id.assert_called_once()
    mock_registry.get_model_metadata.assert_called_once_with("model_123")


def test_list_models(model_manager, mock_registry):
    """Test listing models."""
    # Mock the registry to return a list of models
    models = [
        {
            "id": "model_123",
            "version": "v1.0.0",
            "description": "Test model 1"
        },
        {
            "id": "model_456",
            "version": "v2.0.0",
            "description": "Test model 2"
        }
    ]
    mock_registry.list_models.return_value = models
    
    # List models
    result = model_manager.list_models()
    
    # Check that the correct list was returned
    assert result == models
    mock_registry.list_models.assert_called_once()


def test_list_experiments(model_manager, mock_registry):
    """Test listing experiments."""
    # Mock the registry to return a list of experiments
    experiments = [
        {
            "id": "exp_123",
            "name": "Test Experiment 1",
            "model_ids": ["model_123", "model_456"],
            "traffic_split": [50, 50],
            "status": "active"
        },
        {
            "id": "exp_456",
            "name": "Test Experiment 2",
            "model_ids": ["model_123", "model_789"],
            "traffic_split": [30, 70],
            "status": "stopped"
        }
    ]
    mock_registry.list_experiments.return_value = experiments
    
    # List experiments
    result = model_manager.list_experiments()
    
    # Check that the correct list was returned
    assert result == experiments
    mock_registry.list_experiments.assert_called_once()