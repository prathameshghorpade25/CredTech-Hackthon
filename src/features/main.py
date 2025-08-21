import pandas as pd
import os
from pathlib import Path
from typing import Dict, Optional

from src.features.processor import FeatureProcessor, save_features
from src.utils.io import load_df

def run_feature_engineering(
    structured_data_path: str = 'data/processed/combined_data.csv',
    news_data_path: str = 'data/processed/news_data.csv',
    output_path: str = 'data/processed/features.csv'
) -> Dict:
    """Run the feature engineering pipeline"""
    # Load data
    structured_df = load_df(structured_data_path)
    
    # Load news data if available
    news_df = None
    if os.path.exists(news_data_path):
        news_df = load_df(news_data_path)
    
    # Initialize feature processor
    processor = FeatureProcessor()
    
    # Process features
    features_df = processor.fit_transform(structured_df, news_df)
    
    # Save processed features
    save_features(features_df, output_path)
    
    return {
        "features_df": features_df,
        "processor": processor
    }

if __name__ == "__main__":
    run_feature_engineering()