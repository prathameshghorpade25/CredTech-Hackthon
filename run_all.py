#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CredTech XScore - Explainable Credit Scoring Pipeline

This script orchestrates the full pipeline:
1. Data ingestion from structured and unstructured sources
2. Feature engineering
3. Model training with explainability
4. Metrics calculation and visualization

The pipeline is fully reproducible and configurable through the central config module.
"""

import os
import sys
import argparse
import random
import numpy as np
import json
from datetime import datetime
from pathlib import Path

# Import configuration
from src.utils.config import SEED, MODEL_CONFIG, DATA_PATHS, MODEL_PATHS, REPORT_PATHS, create_directories
from src.utils.logging import get_app_logger

# Set up logger
logger = get_app_logger(__name__)

# Set random seeds for reproducibility
random.seed(SEED)
np.random.seed(SEED)

# Create necessary directories
create_directories()

# Import project modules
from src.ingest.main import run_ingestion
from src.features.main import run_feature_engineering
from src.model.main import run_model_training

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="CredTech XScore Pipeline")
    parser.add_argument(
        "--skip-ingestion", 
        action="store_true", 
        help="Skip data ingestion step"
    )
    parser.add_argument(
        "--skip-features", 
        action="store_true", 
        help="Skip feature engineering step"
    )
    parser.add_argument(
        "--skip-training", 
        action="store_true", 
        help="Skip model training step"
    )
    parser.add_argument(
        "--test-size", 
        type=float, 
        default=MODEL_CONFIG['test_size'], 
        help=f"Test set size (default: {MODEL_CONFIG['test_size']})"
    )
    parser.add_argument(
        "--random-state", 
        type=int, 
        default=SEED, 
        help=f"Random state (default: {SEED})"
    )
    parser.add_argument(
        "--cv", 
        action="store_true", 
        help="Enable cross-validation"
    )
    parser.add_argument(
        "--cv-folds", 
        type=int, 
        default=MODEL_CONFIG['cv_folds'], 
        help=f"Number of cross-validation folds (default: {MODEL_CONFIG['cv_folds']})"
    )
    
    return parser.parse_args()

def main():
    """Run the full pipeline"""
    args = parse_args()
    
    logger.info("="*80)
    logger.info("CredTech XScore - Explainable Credit Scoring Pipeline")
    logger.info("="*80)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Random seed: {args.random_state}")
    logger.info("-"*80)
    
    # Step 1: Data Ingestion
    if not args.skip_ingestion:
        logger.info("\n[1/3] Running data ingestion...")
        try:
            ingestion_results = run_ingestion(
                output_path=DATA_PATHS['structured_data']
            )
            logger.info(f"Data ingestion complete. Structured data: {ingestion_results['structured_data'].shape[0]} rows")
        except Exception as e:
            logger.error(f"Error during data ingestion: {str(e)}")
            return
    else:
        logger.info("\n[1/3] Skipping data ingestion.")
    
    # Step 2: Feature Engineering
    if not args.skip_features:
        logger.info("\n[2/3] Running feature engineering...")
        try:
            feature_results = run_feature_engineering(
                structured_data_path=DATA_PATHS['structured_data'],
                news_data_path=DATA_PATHS['news_data'],
                output_path=DATA_PATHS['features_data']
            )
            logger.info(f"Feature engineering complete. Features shape: {feature_results['features_df'].shape}")
        except Exception as e:
            logger.error(f"Error during feature engineering: {str(e)}")
            return
    else:
        logger.info("\n[2/3] Skipping feature engineering.")
    
    # Step 3: Model Training
    if not args.skip_training:
        logger.info("\n[3/3] Running model training...")
        try:
            model_results = run_model_training(
                features_path=DATA_PATHS['features_data'],
                model_output_dir=MODEL_PATHS['model_dir'],
                test_size=args.test_size,
                time_split=MODEL_CONFIG['time_split'],
                random_state=args.random_state,
                cv_enabled=args.cv,
                cv_folds=args.cv_folds
            )
            
            # Log metrics
            metrics = model_results['results']['metrics']
            logger.info("Model training complete with metrics:")
            logger.info(f"ROC-AUC: {metrics['roc_auc']:.4f}")
            logger.info(f"PR-AUC: {metrics['pr_auc']:.4f}")
            logger.info(f"Brier score: {metrics['brier']:.4f}")
            logger.info(f"K-S statistic: {metrics['ks']:.4f}")
            
            # Save explanation artifacts
            explanation_dir = REPORT_PATHS['explain_dir']
            Path(explanation_dir).mkdir(parents=True, exist_ok=True)
            
            # Save per-issuer explanations
            X_test = model_results['results']['X_test']
            for issuer in X_test['issuer'].unique():
                issuer_data = X_test[X_test['issuer'] == issuer]
                if len(issuer_data) > 0:
                    issuer_explanation = model_results['model'].explain_issuer(issuer_data)
                    with open(os.path.join(explanation_dir, f"{issuer}.json"), 'w') as f:
                        json.dump(issuer_explanation, f, indent=2)
            
            logger.info(f"Saved model to {MODEL_PATHS['model_file']}")
            logger.info(f"Saved metrics to {REPORT_PATHS['metrics_file']}")
            logger.info(f"Saved explanations to {explanation_dir}")
            
        except Exception as e:
            logger.error(f"Error during model training: {str(e)}")
            return
    else:
        logger.info("\n[3/3] Skipping model training.")
        
    logger.info("\nPipeline completed successfully!")
    logger.info(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    print("="*80)
    print("CredTech XScore Pipeline Complete!")
    print("="*80)
    print("\nTo run the Streamlit demo app:")
    print("  streamlit run src/serve/app.py")
    print("\nOr use Docker:")
    print("  docker-compose up streamlit")
    print("="*80)

if __name__ == "__main__":
    main()



