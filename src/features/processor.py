import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os
from pathlib import Path

class FeatureProcessor:
    """Process raw data into features for model training"""
    
    def __init__(self):
        self.feature_columns = []
        self.categorical_features = []
        self.numerical_features = []
    
    def fit_transform(self, structured_df: pd.DataFrame, news_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Process raw data into features"""
        # Make a copy to avoid modifying the original
        df = structured_df.copy()
        
        # Basic feature engineering on structured data
        df = self._process_structured_data(df)
        
        # Merge news data if available
        if news_df is not None and not news_df.empty:
            df = self._merge_news_data(df, news_df)
        
        # Store feature column names for later use
        self._update_feature_lists(df)
        
        return df
    
    def transform(self, structured_df: pd.DataFrame, news_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Transform new data using the same process"""
        # Make a copy to avoid modifying the original
        df = structured_df.copy()
        
        # Apply the same transformations
        df = self._process_structured_data(df)
        
        # Merge news data if available
        if news_df is not None and not news_df.empty:
            df = self._merge_news_data(df, news_df)
        
        # Ensure all expected columns are present
        for col in self.feature_columns:
            if col not in df.columns and col != 'target':
                print(f"Warning: Feature {col} is missing, filling with zeros")
                df[col] = 0
                
        # Ensure all issuer columns are present
        issuers = ['ABC', 'LMN', 'QRS', 'XYZ']
        for issuer in issuers:
            col_name = f'issuer_{issuer}'
            if col_name not in df.columns:
                df[col_name] = 0
                
        # Set the correct issuer column to 1
        if 'issuer' in df.columns:
            for idx, row in df.iterrows():
                issuer_col = f"issuer_{row['issuer']}"
                if issuer_col in df.columns:
                    df.at[idx, issuer_col] = 1
        
        return df
    
    def _process_structured_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process structured data features"""
        # Convert date to datetime if it's not already
        if 'asof_date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['asof_date']):
            df['asof_date'] = pd.to_datetime(df['asof_date'])
        
        # Extract date features
        df['month'] = df['asof_date'].dt.month
        df['day_of_week'] = df['asof_date'].dt.dayofweek
        df['day_of_month'] = df['asof_date'].dt.day
        
        # Create ratio features
        if 'balance' in df.columns and 'income' in df.columns:
            df['balance_to_income'] = df['balance'] / df['income'].replace(0, 1)
        
        if 'transactions' in df.columns and 'income' in df.columns:
            df['transactions_to_income'] = df['transactions'] / (df['income'] / 10000)
        
        # One-hot encode categorical variables
        if 'issuer' in df.columns:
            issuer_dummies = pd.get_dummies(df['issuer'], prefix='issuer')
            df = pd.concat([df, issuer_dummies], axis=1)
        
        return df
    
    def _merge_news_data(self, structured_df: pd.DataFrame, news_df: pd.DataFrame) -> pd.DataFrame:
        """Merge news data with structured data"""
        # Ensure date columns are datetime
        if 'asof_date' in structured_df.columns and not pd.api.types.is_datetime64_any_dtype(structured_df['asof_date']):
            structured_df['asof_date'] = pd.to_datetime(structured_df['asof_date'])
            
        if 'asof_date' in news_df.columns and not pd.api.types.is_datetime64_any_dtype(news_df['asof_date']):
            news_df['asof_date'] = pd.to_datetime(news_df['asof_date'])
        
        # Create a window for news data (e.g., use news from the past 7 days)
        result_df = structured_df.copy()
        
        # For each row in structured data, find relevant news
        sentiment_cols = ['news_sentiment_neg', 'news_sentiment_neu', 'news_sentiment_pos', 'news_sentiment_compound']
        
        # Initialize news sentiment columns with zeros
        for col in sentiment_cols:
            result_df[col] = 0.0
        
        # For each issuer and date, find the most recent news
        for idx, row in structured_df.iterrows():
            issuer = row['issuer']
            date = row['asof_date']
            
            # Find news for this issuer within the past 7 days
            relevant_news = news_df[
                (news_df['issuer'] == issuer) & 
                (news_df['asof_date'] <= date) & 
                (news_df['asof_date'] >= date - timedelta(days=7))
            ]
            
            if not relevant_news.empty:
                # Use the most recent news sentiment
                latest_news = relevant_news.sort_values('asof_date', ascending=False).iloc[0]
                
                for col in sentiment_cols:
                    if col in latest_news:
                        result_df.at[idx, col] = latest_news[col]
        
        return result_df
    
    def _update_feature_lists(self, df: pd.DataFrame):
        """Update the lists of feature columns"""
        # Exclude non-feature columns
        exclude_cols = ['target', 'asof_date', 'data_source', 'issuer', 'news_text']
        
        # Get all potential feature columns
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Identify categorical and numerical features
        categorical = []
        numerical = []
        
        for col in feature_cols:
            if col.startswith('issuer_'):
                categorical.append(col)
            else:
                numerical.append(col)
        
        self.feature_columns = feature_cols
        self.categorical_features = categorical
        self.numerical_features = numerical

def save_features(df: pd.DataFrame, output_path: str = 'data/processed/features.csv'):
    """Save processed features to CSV"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved features to {output_path}")

def load_features(input_path: str = 'data/processed/features.csv') -> pd.DataFrame:
    """Load processed features from CSV"""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Features file not found: {input_path}")
    
    return pd.read_csv(input_path)