import os
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.processor import FeatureProcessor

class TestFeatureProcessor(unittest.TestCase):
    """Test cases for the FeatureProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a sample DataFrame for testing
        self.sample_data = pd.DataFrame({
            'issuer': ['ABC', 'XYZ', 'LMN', 'QRS'],
            'asof_date': ['2023-01-15', '2023-02-20', '2023-03-25', '2023-04-30'],
            'income': [75000, 120000, 45000, 90000],
            'balance': [15000, 30000, 5000, 20000],
            'transactions': [12, 25, 8, 15],
            'news_sentiment_compound': [0.5, -0.3, 0.2, 0.0],
            'news_sentiment_neg': [0.1, 0.4, 0.2, 0.3],
            'news_sentiment_pos': [0.6, 0.1, 0.4, 0.3],
            'news_sentiment_neu': [0.3, 0.5, 0.4, 0.4],
            'data_source': ['test', 'test', 'test', 'test']
        })
        
        # Convert date strings to datetime objects
        self.sample_data['asof_date'] = pd.to_datetime(self.sample_data['asof_date'])
        
        # Initialize the processor
        self.processor = FeatureProcessor()
    
    def test_initialization(self):
        """Test that the processor initializes correctly"""
        self.assertIsInstance(self.processor, FeatureProcessor)
        self.assertEqual(self.processor.non_feature_columns, ['asof_date', 'data_source', 'issuer', 'news_text'])
        self.assertEqual(self.processor.categorical_prefix, 'issuer_')
    
    def test_transform(self):
        """Test the transform method"""
        # Transform the sample data
        transformed_data = self.processor.transform(self.sample_data)
        
        # Check that the DataFrame was returned
        self.assertIsInstance(transformed_data, pd.DataFrame)
        
        # Check that date features were created
        self.assertIn('month', transformed_data.columns)
        self.assertIn('day_of_week', transformed_data.columns)
        self.assertIn('day_of_month', transformed_data.columns)
        
        # Check that ratio features were created
        self.assertIn('balance_to_income', transformed_data.columns)
        self.assertIn('transactions_to_income', transformed_data.columns)
        
        # Check that one-hot encoding was applied for issuers
        self.assertIn('issuer_ABC', transformed_data.columns)
        self.assertIn('issuer_XYZ', transformed_data.columns)
        self.assertIn('issuer_LMN', transformed_data.columns)
        self.assertIn('issuer_QRS', transformed_data.columns)
        
        # Check the values of the one-hot encoded columns
        self.assertEqual(transformed_data.loc[0, 'issuer_ABC'], 1)
        self.assertEqual(transformed_data.loc[0, 'issuer_XYZ'], 0)
        self.assertEqual(transformed_data.loc[1, 'issuer_XYZ'], 1)
        self.assertEqual(transformed_data.loc[1, 'issuer_ABC'], 0)
    
    def test_date_features(self):
        """Test that date features are correctly extracted"""
        # Transform the sample data
        transformed_data = self.processor.transform(self.sample_data)
        
        # Check month extraction
        self.assertEqual(transformed_data.loc[0, 'month'], 1)  # January
        self.assertEqual(transformed_data.loc[1, 'month'], 2)  # February
        
        # Check day of week extraction (0=Monday, 6=Sunday)
        # 2023-01-15 was a Sunday (6)
        self.assertEqual(transformed_data.loc[0, 'day_of_week'], 6)
        
        # Check day of month extraction
        self.assertEqual(transformed_data.loc[0, 'day_of_month'], 15)
        self.assertEqual(transformed_data.loc[1, 'day_of_month'], 20)
    
    def test_ratio_features(self):
        """Test that ratio features are correctly calculated"""
        # Transform the sample data
        transformed_data = self.processor.transform(self.sample_data)
        
        # Check balance to income ratio
        self.assertAlmostEqual(transformed_data.loc[0, 'balance_to_income'], 15000/75000)
        self.assertAlmostEqual(transformed_data.loc[1, 'balance_to_income'], 30000/120000)
        
        # Check transactions to income ratio
        self.assertAlmostEqual(transformed_data.loc[0, 'transactions_to_income'], 12/75000)
        self.assertAlmostEqual(transformed_data.loc[1, 'transactions_to_income'], 25/120000)
    
    def test_missing_issuer(self):
        """Test handling of an issuer not seen during training"""
        # Create data with a new issuer
        new_data = pd.DataFrame({
            'issuer': ['NEW'],
            'asof_date': ['2023-05-15'],
            'income': [60000],
            'balance': [12000],
            'transactions': [10],
            'news_sentiment_compound': [0.1],
            'news_sentiment_neg': [0.2],
            'news_sentiment_pos': [0.3],
            'news_sentiment_neu': [0.5],
            'data_source': ['test']
        })
        new_data['asof_date'] = pd.to_datetime(new_data['asof_date'])
        
        # Transform the data
        transformed_data = self.processor.transform(new_data)
        
        # Check that all issuer columns exist and are set to 0
        self.assertEqual(transformed_data.loc[0, 'issuer_ABC'], 0)
        self.assertEqual(transformed_data.loc[0, 'issuer_XYZ'], 0)
        self.assertEqual(transformed_data.loc[0, 'issuer_LMN'], 0)
        self.assertEqual(transformed_data.loc[0, 'issuer_QRS'], 0)
    
    def test_save_load_features(self):
        """Test saving and loading feature lists"""
        # Create a temporary directory for testing
        import tempfile
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'features.json')
        
        # Set some feature lists
        self.processor.categorical_features = ['cat1', 'cat2']
        self.processor.numerical_features = ['num1', 'num2']
        
        # Save the features
        self.processor.save_features(temp_file)
        
        # Create a new processor
        new_processor = FeatureProcessor()
        
        # Load the features
        new_processor.load_features(temp_file)
        
        # Check that the features were loaded correctly
        self.assertEqual(new_processor.categorical_features, ['cat1', 'cat2'])
        self.assertEqual(new_processor.numerical_features, ['num1', 'num2'])
        
        # Clean up
        os.remove(temp_file)
        os.rmdir(temp_dir)

if __name__ == '__main__':
    unittest.main()