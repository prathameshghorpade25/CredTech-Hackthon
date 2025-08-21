#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Central configuration module for CredTech XScore

This module provides centralized configuration management for the entire project,
including paths, model parameters, and other settings.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Project root directory
ROOT_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Random seed for reproducibility
SEED = 42

# Data paths
DATA_PATHS = {
    'raw_dir': os.path.join(ROOT_DIR, 'data', 'raw'),
    'processed_dir': os.path.join(ROOT_DIR, 'data', 'processed'),
    'structured_data': os.path.join(ROOT_DIR, 'data', 'processed', 'combined_data.csv'),
    'news_data': os.path.join(ROOT_DIR, 'data', 'processed', 'news_data.csv'),
    'features_data': os.path.join(ROOT_DIR, 'data', 'processed', 'features.csv'),
}

# Model paths
MODEL_PATHS = {
    'model_dir': os.path.join(ROOT_DIR, 'models'),
    'model_file': os.path.join(ROOT_DIR, 'models', 'model.joblib'),
}

# Reports paths
REPORT_PATHS = {
    'reports_dir': os.path.join(ROOT_DIR, 'reports'),
    'figures_dir': os.path.join(ROOT_DIR, 'reports', 'figures'),
    'metrics_file': os.path.join(ROOT_DIR, 'reports', 'metrics.json'),
    'explain_dir': os.path.join(ROOT_DIR, 'reports', 'explain'),
}

# Logs path
LOGS_DIR = os.path.join(ROOT_DIR, 'logs')

# Feature engineering settings
FEATURE_CONFIG = {
    'non_feature_columns': ['asof_date', 'data_source', 'issuer', 'news_text'],
    'categorical_prefix': 'issuer_',
    'short_term_window': 30,  # days for short-term features
    'long_term_window': 90,   # days for long-term features
}

# Model training settings
MODEL_CONFIG = {
    'test_size': 0.2,
    'time_split': True,  # Use time-based split instead of random
    'cv_folds': 5,      # Number of cross-validation folds
    'lightgbm_params': {
        'n_estimators': 100,
        'learning_rate': 0.1,
        'max_depth': 5,
        'early_stopping_rounds': 10,
        'random_state': SEED,
    },
    'calibration_method': 'isotonic',  # 'isotonic' or 'sigmoid'
}

# Score bands configuration
SCORE_BANDS = {
    'A': {'min': 0.8, 'max': 1.0, 'description': 'Very Low Risk', 'color': '#008000'},
    'B': {'min': 0.6, 'max': 0.8, 'description': 'Low Risk', 'color': '#90EE90'},
    'C': {'min': 0.4, 'max': 0.6, 'description': 'Moderate Risk', 'color': '#FFFF00'},
    'D': {'min': 0.2, 'max': 0.4, 'description': 'High Risk', 'color': '#FFA500'},
    'E': {'min': 0.0, 'max': 0.2, 'description': 'Very High Risk', 'color': '#FF0000'},
}

# API configuration for data ingestion
API_CONFIG = {
    'max_retries': 3,
    'retry_delay': 5,  # seconds
    'timeout': 30,     # seconds
}

# Reason code templates for explainability
REASON_CODE_TEMPLATES = {
    'positive': {
        'income': 'Strong income profile',
        'balance': 'Healthy account balance',
        'transactions': 'Consistent transaction history',
        'news_sentiment_compound': 'Positive news sentiment',
        'news_sentiment_pos': 'Favorable media coverage',
    },
    'negative': {
        'income': 'Below average income profile',
        'balance': 'Low account balance',
        'transactions': 'Irregular transaction pattern',
        'news_sentiment_compound': 'Negative news sentiment',
        'news_sentiment_neg': 'Unfavorable media coverage',
    }
}

# Create directories if they don't exist
def create_directories():
    """Create necessary directories if they don't exist"""
    for path_dict in [DATA_PATHS, MODEL_PATHS, REPORT_PATHS]:
        for _, path in path_dict.items():
            if isinstance(path, str) and not path.endswith('.csv') and not path.endswith('.json') and not path.endswith('.joblib'):
                os.makedirs(path, exist_ok=True)
    
    # Create logs directory
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Create explanation directory
    os.makedirs(REPORT_PATHS['explain_dir'], exist_ok=True)