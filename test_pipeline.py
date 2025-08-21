#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to verify the credit scoring pipeline works correctly.
This script runs each component of the pipeline separately and checks for expected outputs.
"""

import os
import sys
import argparse
import pandas as pd
import joblib
import json
from pathlib import Path

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.ingest.main import run_ingestion
from src.features.main import run_feature_engineering
from src.model.main import run_model_training


def test_ingestion():
    """Test the data ingestion module"""
    print("\n=== Testing Data Ingestion ===\n")
    
    # Run ingestion
    run_ingestion()
    
    # Check if output files exist
    structured_path = Path("data/processed/combined_data.csv")
    news_path = Path("data/processed/news_data.csv")
    
    if structured_path.exists() and news_path.exists():
        print("✓ Ingestion successful: Output files created")
        
        # Check data content
        structured_data = pd.read_csv(structured_path)
        news_data = pd.read_csv(news_path)
        
        print("  - Structured data shape: {}".format(structured_data.shape))
        print("  - News data shape: {}".format(news_data.shape))
        
        # Check for required columns
        required_cols = ['issuer', 'asof_date', 'income', 'balance', 'transactions', 'target']
        missing_cols = [col for col in required_cols if col not in structured_data.columns]
        
        if not missing_cols:
            print("✓ All required columns present in structured data")
        else:
            print("✗ Missing columns in structured data: {}".format(missing_cols))
            
        return True
    else:
        print("✗ Ingestion failed: Output files not created")
        return False


def test_feature_engineering():
    """Test the feature engineering module"""
    print("\n=== Testing Feature Engineering ===\n")
    
    # Run feature engineering
    run_feature_engineering()
    
    # Check if output file exists
    features_path = Path("data/processed/features.csv")
    
    if features_path.exists():
        print("✓ Feature engineering successful: Output file created")
        
        # Check data content
        features = pd.read_csv(features_path)
        print("  - Features shape: {}".format(features.shape))
        
        # Check for engineered features
        expected_features = ['month', 'day_of_week', 'balance_income_ratio', 'news_sentiment']
        missing_features = [feat for feat in expected_features if not any(col.startswith(feat) for col in features.columns)]
        
        if not missing_features:
            print("✓ All expected engineered features present")
        else:
            print("✗ Missing engineered features: {}".format(missing_features))
            
        return True
    else:
        print("✗ Feature engineering failed: Output file not created")
        return False


def test_model_training():
    """Test the model training module"""
    print("\n=== Testing Model Training ===\n")
    
    # Run model training
    run_model_training()
    
    # Check if output files exist
    model_path = Path("models/model.joblib")
    metrics_path = Path("reports/metrics.json")
    figures_path = Path("reports/figures")
    
    success = True
    
    if model_path.exists():
        print("✓ Model training successful: Model file created")
        
        # Load model to verify
        try:
            model = joblib.load(model_path)
            print("  - Model type: {}".format(type(model).__name__))
        except Exception as e:
            print("✗ Error loading model: {}".format(e))
            success = False
    else:
        print("✗ Model training failed: Model file not created")
        success = False
        
    if metrics_path.exists():
        print("✓ Metrics file created")
        
        # Load metrics to verify
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            print("  - Metrics: {}".format(', '.join(metrics.keys())))
            
            # Check for required metrics
            required_metrics = ['roc_auc', 'pr_auc', 'brier_score', 'ks_stat']
            missing_metrics = [metric for metric in required_metrics if metric not in metrics]
            
            if not missing_metrics:
                print("✓ All required metrics present")
            else:
                print("✗ Missing metrics: {}".format(missing_metrics))
                success = False
        except Exception as e:
            print("✗ Error loading metrics: {}".format(e))
            success = False
    else:
        print("✗ Metrics file not created")
        success = False
        
    if figures_path.exists() and any(figures_path.iterdir()):
        print("✓ Figure files created")
        print("  - Number of figures: {}".format(len(list(figures_path.iterdir()))))
    else:
        print("✗ Figure files not created or directory empty")
        success = False
        
    return success


def main():
    parser = argparse.ArgumentParser(description='Test the credit scoring pipeline')
    parser.add_argument('--component', choices=['ingestion', 'features', 'model', 'all'], 
                        default='all', help='Pipeline component to test')
    args = parser.parse_args()
    
    # Create necessary directories if they don't exist
    for dir_path in ['data/processed', 'models', 'reports/figures']:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    success = True
    
    if args.component == 'ingestion' or args.component == 'all':
        success = test_ingestion() and success
        
    if args.component == 'features' or args.component == 'all':
        success = test_feature_engineering() and success
        
    if args.component == 'model' or args.component == 'all':
        success = test_model_training() and success
    
    print("\n=== Test Summary ===\n")
    if success:
        print("✓ All tests passed successfully!")
        return 0
    else:
        print("✗ Some tests failed. See details above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())