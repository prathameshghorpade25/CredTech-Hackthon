import os
import sys
import unittest
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model.trainer import CreditScoreModel

class TestCreditScoreModel(unittest.TestCase):
    """Test cases for the CreditScoreModel class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a sample DataFrame for testing
        self.sample_data = pd.DataFrame({
            'issuer': ['ABC', 'XYZ', 'LMN', 'QRS', 'ABC'],
            'asof_date': ['2023-01-15', '2023-02-20', '2023-03-25', '2023-04-30', '2023-05-05'],
            'income': [75000, 120000, 45000, 90000, 60000],
            'balance': [15000, 30000, 5000, 20000, 10000],
            'transactions': [12, 25, 8, 15, 10],
            'data_source': ['test', 'test', 'test', 'test', 'test'],
            'month': [1, 2, 3, 4, 5],
            'day_of_week': [6, 1, 5, 0, 5],
            'day_of_month': [15, 20, 25, 30, 5],
            'balance_to_income': [0.2, 0.25, 0.11, 0.22, 0.17],
            'transactions_to_income': [0.00016, 0.00021, 0.00018, 0.00017, 0.00017],
            'issuer_ABC': [1, 0, 0, 0, 1],
            'issuer_XYZ': [0, 1, 0, 0, 0],
            'issuer_LMN': [0, 0, 1, 0, 0],
            'issuer_QRS': [0, 0, 0, 1, 0],
            'news_sentiment_neg': [0.1, 0.4, 0.2, 0.3, 0.2],
            'news_sentiment_pos': [0.6, 0.1, 0.4, 0.3, 0.5],
            'news_sentiment_neu': [0.3, 0.5, 0.4, 0.4, 0.3],
            'news_sentiment_compound': [0.5, -0.3, 0.2, 0.0, 0.3],
            'target': [1, 0, 1, 0, 1]  # Binary target for classification
        })
        
        # Convert date strings to datetime objects
        self.sample_data['asof_date'] = pd.to_datetime(self.sample_data['asof_date'])
        
        # Define feature lists
        self.categorical_features = ['issuer_ABC', 'issuer_XYZ', 'issuer_LMN', 'issuer_QRS']
        self.numerical_features = ['income', 'balance', 'transactions', 'month', 'day_of_week', 
                                  'day_of_month', 'balance_to_income', 'transactions_to_income',
                                  'news_sentiment_neg', 'news_sentiment_pos', 'news_sentiment_neu', 
                                  'news_sentiment_compound']
        
        # Initialize the model
        self.model = CreditScoreModel()
        self.model.categorical_features = self.categorical_features
        self.model.numerical_features = self.numerical_features
    
    def test_initialization(self):
        """Test that the model initializes correctly"""
        self.assertIsInstance(self.model, CreditScoreModel)
        self.assertEqual(self.model.non_feature_columns, ['asof_date', 'data_source', 'issuer', 'news_text'])
        self.assertIsNone(self.model.model)
        self.assertIsNone(self.model.scaler)
        self.assertIsNone(self.model.explainer)
    
    def test_fit(self):
        """Test the fit method"""
        # Fit the model
        self.model.fit(self.sample_data)
        
        # Check that the model was created
        self.assertIsNotNone(self.model.model)
        
        # Check that the scaler was created
        self.assertIsNotNone(self.model.scaler)
        self.assertIsInstance(self.model.scaler, StandardScaler)
        
        # Check that the explainer was created
        self.assertIsNotNone(self.model.explainer)
    
    def test_predict(self):
        """Test the predict method"""
        # Fit the model
        self.model.fit(self.sample_data)
        
        # Create test data (first 2 rows of sample data)
        test_data = self.sample_data.iloc[:2].copy()
        
        # Make predictions
        predictions = self.model.predict(test_data)
        
        # Check that predictions were returned
        self.assertIsNotNone(predictions)
        self.assertEqual(len(predictions), 2)
        
        # Check that predictions are between 0 and 1 (probabilities)
        self.assertTrue(all(0 <= p <= 1 for p in predictions))
    
    def test_explain(self):
        """Test the explain method"""
        # Fit the model
        self.model.fit(self.sample_data)
        
        # Create test data (first 2 rows of sample data)
        test_data = self.sample_data.iloc[:2].copy()
        
        # Get explanations
        explanations = self.model.explain(test_data)
        
        # Check that explanations were returned
        self.assertIsNotNone(explanations)
        self.assertEqual(len(explanations), 2)
        
        # Check that each explanation has the expected structure
        for explanation in explanations:
            self.assertIn('shap_values', explanation)
            self.assertIn('base_value', explanation)
            self.assertIn('feature_names', explanation)
            self.assertIn('feature_values', explanation)
    
    def test_explain_instance(self):
        """Test the explain_instance method"""
        # Fit the model
        self.model.fit(self.sample_data)
        
        # Create test data (first row of sample data)
        test_instance = self.sample_data.iloc[0].copy()
        
        # Get explanation
        explanation = self.model.explain_instance(test_instance)
        
        # Check that explanation was returned
        self.assertIsNotNone(explanation)
        
        # Check that the explanation has the expected structure
        self.assertIn('contributions', explanation)
        self.assertIn('base_value', explanation)
        self.assertIn('score', explanation)
        
        # Check that contributions have the expected structure
        contributions = explanation['contributions']
        self.assertTrue(len(contributions) > 0)
        for contribution in contributions:
            self.assertIn('feature', contribution)
            self.assertIn('value', contribution)
            self.assertIn('contribution', contribution)
    
    def test_save_load_model(self):
        """Test saving and loading the model"""
        # Create a temporary directory for testing
        import tempfile
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'model.joblib')
        
        # Fit the model
        self.model.fit(self.sample_data)
        
        # Save the model
        self.model.save(temp_file)
        
        # Create a new model
        new_model = CreditScoreModel()
        
        # Load the model
        new_model.load(temp_file)
        
        # Check that the model was loaded correctly
        self.assertIsNotNone(new_model.model)
        self.assertIsNotNone(new_model.scaler)
        self.assertEqual(new_model.categorical_features, self.categorical_features)
        self.assertEqual(new_model.numerical_features, self.numerical_features)
        
        # Clean up
        os.remove(temp_file)
        os.rmdir(temp_dir)

if __name__ == '__main__':
    unittest.main()