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
from src.model.trainer import CreditScoreModel


@pytest.fixture
def temp_registry_dir():
    """Create a temporary directory for the model registry."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_model():
    """Create a mock model for testing."""
    model = MagicMock(spec=CreditScoreModel)
    model.model = MagicMock()
    model.feature_names = ["feature1", "feature2", "feature3"]
    model.model_type = "lightgbm"
    model.metrics = {
        "roc_auc": 0.85,
        "pr_auc": 0.75,
        "brier_score": 0.12,
        "ks_stat": 0.65
    }
    return model


@pytest.fixture
def registry(temp_registry_dir):
    """Create a model registry instance."""
    return ModelRegistry(registry_dir=temp_registry_dir)


def test_registry_initialization(registry, temp_registry_dir):
    """Test that the registry is initialized correctly."""
    assert registry.registry_dir == temp_registry_dir
    assert os.path.exists(os.path.join(temp_registry_dir, "models"))
    assert os.path.exists(os.path.join(temp_registry_dir, "experiments"))
    assert os.path.exists(os.path.join(temp_registry_dir, "registry.json"))
    
    # Check that registry.json has the correct structure
    with open(os.path.join(temp_registry_dir, "registry.json"), "r") as f:
        registry_data = json.load(f)
    
    assert "models" in registry_data
    assert "experiments" in registry_data
    assert "production_model_id" in registry_data
    assert registry_data["production_model_id"] is None


def test_register_model(registry, mock_model, temp_registry_dir):
    """Test registering a model."""
    model_id = registry.register_model(
        model=mock_model,
        version="v1.0.0",
        description="Test model",
        metadata={"test_key": "test_value"}
    )
    
    # Check that the model directory was created
    model_dir = os.path.join(temp_registry_dir, "models", model_id)
    assert os.path.exists(model_dir)
    
    # Check that model files were saved
    assert os.path.exists(os.path.join(model_dir, "model.joblib"))
    assert os.path.exists(os.path.join(model_dir, "metadata.json"))
    
    # Check that registry.json was updated
    with open(os.path.join(temp_registry_dir, "registry.json"), "r") as f:
        registry_data = json.load(f)
    
    assert model_id in registry_data["models"]
    assert registry_data["models"][model_id]["version"] == "v1.0.0"
    assert registry_data["models"][model_id]["description"] == "Test model"
    assert registry_data["models"][model_id]["test_key"] == "test_value"


def test_get_model(registry, mock_model, temp_registry_dir):
    """Test getting a model from the registry."""
    # Register a model first
    model_id = registry.register_model(
        model=mock_model,
        version="v1.0.0",
        description="Test model"
    )
    
    # Get the model
    loaded_model = registry.load_model(model_id)
    
    # Check that the model was loaded correctly
    assert loaded_model is not None
    
    # Check that the model metadata was loaded correctly
    model_metadata = registry.get_model_metadata(model_id)
    assert model_metadata["version"] == "v1.0.0"
    assert model_metadata["description"] == "Test model"
    assert model_metadata["feature_names"] == ["feature1", "feature2", "feature3"]
    assert model_metadata["model_type"] == "lightgbm"


def test_promote_model_to_production(registry, mock_model, temp_registry_dir):
    """Test promoting a model to production."""
    # Register a model first
    model_id = registry.register_model(
        model=mock_model,
        version="v1.0.0",
        description="Test model"
    )
    
    # Promote the model to production
    registry.promote_model_to_production(model_id)
    
    # Check that registry.json was updated
    with open(os.path.join(temp_registry_dir, "registry.json"), "r") as f:
        registry_data = json.load(f)
    
    assert registry_data["production_model_id"] == model_id
    
    # Check that get_production_model_id returns the correct ID
    assert registry.get_production_model_id() == model_id


def test_list_models(registry, mock_model, temp_registry_dir):
    """Test listing models in the registry."""
    # Register two models
    model_id1 = registry.register_model(
        model=mock_model,
        version="v1.0.0",
        description="Test model 1"
    )
    
    model_id2 = registry.register_model(
        model=mock_model,
        version="v2.0.0",
        description="Test model 2"
    )
    
    # List models
    models = registry.list_models()
    
    # Check that both models are in the list
    assert len(models) == 2
    assert model_id1 in [model["id"] for model in models]
    assert model_id2 in [model["id"] for model in models]
    
    # Check that model details are correct
    for model in models:
        if model["id"] == model_id1:
            assert model["version"] == "v1.0.0"
            assert model["description"] == "Test model 1"
        elif model["id"] == model_id2:
            assert model["version"] == "v2.0.0"
            assert model["description"] == "Test model 2"


def test_create_experiment(registry, mock_model, temp_registry_dir):
    """Test creating an A/B testing experiment."""
    # Register two models
    model_id1 = registry.register_model(
        model=mock_model,
        version="v1.0.0",
        description="Test model 1"
    )
    
    model_id2 = registry.register_model(
        model=mock_model,
        version="v2.0.0",
        description="Test model 2"
    )
    
    # Create an experiment
    experiment_id = registry.create_experiment(
        name="Test Experiment",
        description="A test experiment",
        model_ids=[model_id1, model_id2],
        traffic_split=[50, 50]
    )
    
    # Check that the experiment directory was created
    experiment_dir = os.path.join(temp_registry_dir, "experiments", experiment_id)
    assert os.path.exists(experiment_dir)
    
    # Check that experiment files were saved
    assert os.path.exists(os.path.join(experiment_dir, "metadata.json"))
    
    # Check that registry.json was updated
    with open(os.path.join(temp_registry_dir, "registry.json"), "r") as f:
        registry_data = json.load(f)
    
    assert experiment_id in registry_data["experiments"]
    assert registry_data["experiments"][experiment_id]["name"] == "Test Experiment"
    assert registry_data["experiments"][experiment_id]["description"] == "A test experiment"
    assert registry_data["experiments"][experiment_id]["model_ids"] == [model_id1, model_id2]
    assert registry_data["experiments"][experiment_id]["traffic_split"] == [50, 50]
    assert registry_data["experiments"][experiment_id]["status"] == "active"


def test_list_experiments(registry, mock_model, temp_registry_dir):
    """Test listing experiments in the registry."""
    # Register two models
    model_id1 = registry.register_model(
        model=mock_model,
        version="v1.0.0",
        description="Test model 1"
    )
    
    model_id2 = registry.register_model(
        model=mock_model,
        version="v2.0.0",
        description="Test model 2"
    )
    
    # Create two experiments
    experiment_id1 = registry.create_experiment(
        name="Test Experiment 1",
        description="A test experiment 1",
        model_ids=[model_id1, model_id2],
        traffic_split=[50, 50]
    )
    
    experiment_id2 = registry.create_experiment(
        name="Test Experiment 2",
        description="A test experiment 2",
        model_ids=[model_id1, model_id2],
        traffic_split=[30, 70]
    )
    
    # List experiments
    experiments = registry.list_experiments()
    
    # Check that both experiments are in the list
    assert len(experiments) == 2
    assert experiment_id1 in [exp["id"] for exp in experiments]
    assert experiment_id2 in [exp["id"] for exp in experiments]
    
    # Check that experiment details are correct
    for exp in experiments:
        if exp["id"] == experiment_id1:
            assert exp["name"] == "Test Experiment 1"
            assert exp["description"] == "A test experiment 1"
            assert exp["model_ids"] == [model_id1, model_id2]
            assert exp["traffic_split"] == [50, 50]
        elif exp["id"] == experiment_id2:
            assert exp["name"] == "Test Experiment 2"
            assert exp["description"] == "A test experiment 2"
            assert exp["model_ids"] == [model_id1, model_id2]
            assert exp["traffic_split"] == [30, 70]


def test_stop_experiment(registry, mock_model, temp_registry_dir):
    """Test stopping an experiment."""
    # Register two models
    model_id1 = registry.register_model(
        model=mock_model,
        version="v1.0.0",
        description="Test model 1"
    )
    
    model_id2 = registry.register_model(
        model=mock_model,
        version="v2.0.0",
        description="Test model 2"
    )
    
    # Create an experiment
    experiment_id = registry.create_experiment(
        name="Test Experiment",
        description="A test experiment",
        model_ids=[model_id1, model_id2],
        traffic_split=[50, 50]
    )
    
    # Stop the experiment
    registry.stop_experiment(experiment_id)
    
    # Check that registry.json was updated
    with open(os.path.join(temp_registry_dir, "registry.json"), "r") as f:
        registry_data = json.load(f)
    
    assert registry_data["experiments"][experiment_id]["status"] == "stopped"
    
    # Check that get_active_experiment returns None
    assert registry.get_active_experiment() is None