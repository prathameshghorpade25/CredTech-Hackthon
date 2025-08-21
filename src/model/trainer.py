import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import os
from pathlib import Path
import joblib
import json
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMClassifier
import shap

from src.utils.metrics import eval_all, save_metrics_plot
from src.utils.io import save_model, save_json

# Ensure this class is properly defined and accessible
class CreditScoreModel:
    """Credit scoring model with explainability"""
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.categorical_features = []
        self.numerical_features = []
        self.explainer = None
    
    def train(
        self, 
        X: pd.DataFrame, 
        y: pd.Series,
        categorical_features: Optional[List[str]] = None,
        numerical_features: Optional[List[str]] = None,
        test_size: float = 0.2,
        time_split: bool = True
    ) -> Dict:
        """Train the model and compute metrics"""
        # Store feature names
        self.feature_names = list(X.columns)
        self.categorical_features = categorical_features or []
        self.numerical_features = numerical_features or []
        
        # Split data into train and test sets
        if time_split and 'asof_date' in X.columns:
            # Sort by date and use the most recent data as test set
            X = X.sort_values('asof_date')
            train_idx = int(len(X) * (1 - test_size))
            X_train, X_test = X.iloc[:train_idx], X.iloc[train_idx:]
            y_train, y_test = y.iloc[:train_idx], y.iloc[train_idx:]
        else:
            # Random split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=self.random_state
            )
        
        # Remove non-feature columns
        drop_cols = ['asof_date', 'data_source', 'issuer', 'news_text']
        X_train = X_train.drop([col for col in drop_cols if col in X_train.columns], axis=1)
        X_test = X_test.drop([col for col in drop_cols if col in X_test.columns], axis=1)
        
        # Scale numerical features
        if self.numerical_features:
            X_train[self.numerical_features] = self.scaler.fit_transform(X_train[self.numerical_features])
            X_test[self.numerical_features] = self.scaler.transform(X_test[self.numerical_features])
        
        # Train the model
        self.model = LGBMClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        # Fit the model
        self.model.fit(
            X_train, 
            y_train,
            categorical_feature=self.categorical_features,
            eval_set=[(X_test, y_test)],
            eval_metric='auc',
            early_stopping_rounds=10,
            verbose=10
        )
        
        # Make predictions
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Compute metrics
        metrics = eval_all(y_test, y_pred_proba)
        
        # Create SHAP explainer
        self.explainer = shap.TreeExplainer(self.model)
        
        # Return results
        return {
            "metrics": metrics,
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
            "y_pred_proba": y_pred_proba
        }
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions on new data"""
        if self.model is None:
            raise ValueError("Model has not been trained yet")
        
        # Prepare features
        X_pred = X.copy()
        
        # Remove non-feature columns
        drop_cols = ['asof_date', 'data_source', 'issuer', 'news_text']
        X_pred = X_pred.drop([col for col in drop_cols if col in X_pred.columns], axis=1)
        
        # Scale numerical features
        if self.numerical_features:
            X_pred[self.numerical_features] = self.scaler.transform(X_pred[self.numerical_features])
        
        # Make predictions
        return self.model.predict_proba(X_pred)[:, 1]
    
    def explain(self, X: pd.DataFrame, max_display: int = 10) -> Dict:
        """Generate SHAP explanations for predictions"""
        if self.model is None or self.explainer is None:
            raise ValueError("Model has not been trained yet")
        
        # Prepare features
        X_explain = X.copy()
        
        # Remove non-feature columns
        drop_cols = ['asof_date', 'data_source', 'issuer', 'news_text']
        X_explain = X_explain.drop([col for col in drop_cols if col in X_explain.columns], axis=1)
        
        # Scale numerical features
        if self.numerical_features:
            X_explain[self.numerical_features] = self.scaler.transform(X_explain[self.numerical_features])
        
        # Generate SHAP values
        shap_values = self.explainer.shap_values(X_explain)
        
        # For binary classification, SHAP returns a list with one element
        if isinstance(shap_values, list):
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        
        # Get feature importance
        feature_importance = np.abs(shap_values).mean(axis=0)
        feature_importance_dict = dict(zip(X_explain.columns, feature_importance))
        
        # Sort features by importance
        sorted_features = sorted(
            feature_importance_dict.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Get top features
        top_features = sorted_features[:max_display]
        
        return {
            "shap_values": shap_values,
            "feature_importance": feature_importance_dict,
            "top_features": top_features,
            "base_value": self.explainer.expected_value
        }
    
    def explain_instance(self, instance: pd.DataFrame) -> Dict:
        """Generate explanation for a single instance"""
        if self.model is None or self.explainer is None:
            raise ValueError("Model has not been trained yet")
        
        # Prepare features
        X_explain = instance.copy()
        
        # Remove non-feature columns
        drop_cols = ['asof_date', 'data_source', 'issuer', 'news_text']
        X_explain = X_explain.drop([col for col in drop_cols if col in X_explain.columns], axis=1)
        
        # Scale numerical features
        if self.numerical_features:
            X_explain[self.numerical_features] = self.scaler.transform(X_explain[self.numerical_features])
        
        # Generate SHAP values
        shap_values = self.explainer.shap_values(X_explain)
        
        # For binary classification, SHAP returns a list with one element
        if isinstance(shap_values, list):
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        
        # Get feature contributions
        feature_contributions = []
        for i, col in enumerate(X_explain.columns):
            contribution = {
                "feature": col,
                "value": float(X_explain.iloc[0, i]),
                "contribution": float(shap_values[0, i])
            }
            feature_contributions.append(contribution)
        
        # Sort by absolute contribution
        feature_contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        
        # Calculate score components
        base_value = self.explainer.expected_value
        if isinstance(base_value, list):
            base_value = base_value[1] if len(base_value) > 1 else base_value[0]
        elif isinstance(base_value, np.ndarray):
            base_value = base_value[1] if len(base_value) > 1 else base_value[0]
        base_value = float(base_value)
        
        total_contribution = sum(item["contribution"] for item in feature_contributions)
        score = base_value + total_contribution
        
        return {
            "base_value": base_value,
            "contributions": feature_contributions,
            "score": score
        }

def save_training_artifacts(model: CreditScoreModel, results: Dict, output_dir: str = 'models', version: str = None, register: bool = False):
    """Save model and training artifacts
    
    Args:
        model: Trained model to save
        results: Dictionary of training results
        output_dir: Directory to save model artifacts
        version: Model version (if None, will use timestamp)
        register: Whether to register the model in the registry
    
    Returns:
        model_path: Path to the saved model
        model_id: ID of the registered model (if register=True)
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate version if not provided
    if version is None:
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save model
    model_path = os.path.join(output_dir, f"model_{version}.joblib")
    save_model(model, model_path)
    
    # Save metrics
    metrics_path = os.path.join('reports', f"metrics_{version}.json")
    save_json(results["metrics"], metrics_path)
    
    # Save plots
    save_metrics_plot(results["y_test"], results["y_pred_proba"], suffix=version)
    
    print(f"Saved model to {model_path}")
    print(f"Saved metrics to {metrics_path}")
    print(f"Saved plots to reports/figures/")
    
    # Register model if requested
    model_id = None
    if register:
        try:
            from src.model.registry import ModelRegistry
            registry = ModelRegistry()
            
            # Create metadata
            metadata = {
                "feature_names": model.feature_names,
                "categorical_features": model.categorical_features,
                "numerical_features": model.numerical_features,
                "training_date": datetime.now().isoformat(),
                "model_type": type(model.model).__name__,
                "model_params": model.model.get_params()
            }
            
            # Register model
            model_id = registry.register_model(
                model_path=model_path,
                model_name="CreditScoreModel",
                version=version,
                metrics=results["metrics"],
                description=f"Credit score model trained on {datetime.now().strftime('%Y-%m-%d')}",
                metadata=metadata
            )
            
            print(f"Registered model in registry with ID: {model_id}")
        except Exception as e:
            print(f"Failed to register model: {str(e)}")
    
    return model_path, model_id