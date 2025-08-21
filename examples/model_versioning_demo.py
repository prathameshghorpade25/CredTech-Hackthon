#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Model Versioning and A/B Testing Demo

This script demonstrates how to use the model versioning and A/B testing capabilities
of the CredTech XScore system.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model.main import run_model_training, list_models, create_experiment
from src.model.registry import ModelRegistry
from src.serve.model_manager import ModelManager


def train_models():
    """Train multiple model versions with different configurations."""
    print("\n=== Training Model Versions ===")
    
    # Train the first model version (baseline)
    print("\nTraining baseline model (v1.0.0)...")
    model_id1 = run_model_training(
        version="v1.0.0",
        register=True,
        promote_to_production=True,
        description="Baseline model with default features"
    )
    print(f"Baseline model registered with ID: {model_id1}")
    
    # Train the second model version (with feature engineering changes)
    print("\nTraining enhanced model (v1.1.0)...")
    model_id2 = run_model_training(
        version="v1.1.0",
        register=True,
        description="Enhanced model with additional feature engineering",
        # Here you could add parameters to modify feature engineering
    )
    print(f"Enhanced model registered with ID: {model_id2}")
    
    return model_id1, model_id2


def list_available_models():
    """List all available models in the registry."""
    print("\n=== Available Models ===")
    models = list_models()
    
    for model in models:
        print(f"\nModel ID: {model['id']}")
        print(f"Version: {model['version']}")
        print(f"Description: {model['description']}")
        print(f"Training Date: {model['training_date']}")
        print(f"Production: {'Yes' if model.get('is_production', False) else 'No'}")
        
        # Print metrics if available
        if 'metrics' in model:
            print("Metrics:")
            for metric_name, metric_value in model['metrics'].items():
                print(f"  {metric_name}: {metric_value:.4f}")


def setup_ab_testing(model_id1, model_id2):
    """Set up an A/B testing experiment between two models."""
    print("\n=== Setting Up A/B Testing ===")
    
    experiment_id = create_experiment(
        name="Feature Engineering Comparison",
        description="Comparing baseline model with enhanced feature engineering",
        model_ids=[model_id1, model_id2],
        traffic_split=[50, 50]
    )
    
    print(f"A/B testing experiment created with ID: {experiment_id}")
    return experiment_id


def simulate_predictions():
    """Simulate making predictions with the model manager."""
    print("\n=== Simulating Predictions ===")
    
    # Create a model manager
    model_manager = ModelManager()
    
    # Create some sample data
    data = {
        'loan_amnt': [10000, 20000, 15000, 5000],
        'term': [36, 60, 36, 60],
        'int_rate': [5.32, 10.78, 7.42, 12.62],
        'installment': [300, 450, 350, 120],
        'grade': ['A', 'C', 'B', 'D'],
        'emp_length': [5, 10, 3, 1],
        'home_ownership': ['RENT', 'OWN', 'MORTGAGE', 'RENT'],
        'annual_inc': [60000, 85000, 75000, 35000],
        'verification_status': ['Verified', 'Not Verified', 'Verified', 'Not Verified'],
        'purpose': ['debt_consolidation', 'home_improvement', 'credit_card', 'small_business'],
        'dti': [18.2, 22.4, 15.8, 28.3],
        'delinq_2yrs': [0, 1, 0, 2],
        'earliest_cr_line': ['2010-01-01', '2005-03-15', '2012-07-01', '2015-12-01'],
        'open_acc': [3, 12, 6, 2],
        'pub_rec': [0, 0, 1, 0],
        'revol_bal': [15000, 25000, 12000, 5000],
        'revol_util': [35.2, 78.5, 42.3, 65.1],
        'total_acc': [10, 25, 15, 5],
        'initial_list_status': ['w', 'f', 'w', 'f'],
        'application_type': ['Individual', 'Individual', 'Joint', 'Individual'],
        'mort_acc': [1, 3, 0, 0],
        'pub_rec_bankruptcies': [0, 0, 0, 1]
    }
    
    features = pd.DataFrame(data)
    
    # Make predictions with different request IDs to simulate A/B testing
    print("\nMaking predictions with different request IDs:")
    for i, request_id in enumerate([f"request_{i}" for i in range(10)]):
        result = model_manager.predict_with_explanation(
            features,
            request_id=request_id
        )
        
        # Get the first prediction for demonstration
        score = result["scores"][0]
        model_id = result.get("model_id", "unknown")
        
        print(f"Request {i+1}: Score = {score:.4f}, Model = {model_id}")


def main():
    """Run the model versioning and A/B testing demo."""
    print("\n===== CredTech XScore: Model Versioning and A/B Testing Demo =====")
    
    parser = argparse.ArgumentParser(description="Demonstrate model versioning and A/B testing capabilities")
    parser.add_argument("--skip-training", action="store_true", help="Skip model training step")
    args = parser.parse_args()
    
    if not args.skip_training:
        # Train multiple model versions
        model_id1, model_id2 = train_models()
    else:
        # Use existing models (assuming they exist)
        registry = ModelRegistry()
        models = registry.list_models()
        if len(models) < 2:
            print("Error: Need at least two models in the registry. Run without --skip-training.")
            return
        model_id1 = models[0]["id"]
        model_id2 = models[1]["id"]
    
    # List available models
    list_available_models()
    
    # Set up A/B testing
    experiment_id = setup_ab_testing(model_id1, model_id2)
    
    # Simulate predictions
    simulate_predictions()
    
    print("\n===== Demo Complete =====")
    print("\nNext steps:")
    print("1. Use the model_manager_cli.py script to manage models and experiments")
    print("2. Access the API endpoints for model versioning and A/B testing")
    print("3. Check the model_versioning_guide.md for more information")


if __name__ == "__main__":
    main()