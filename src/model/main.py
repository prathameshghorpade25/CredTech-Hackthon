import pandas as pd
import os
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

from src.model.trainer import CreditScoreModel, save_training_artifacts
from src.model.registry import ModelRegistry
from src.utils.io import load_df
from src.utils.logging import get_app_logger

# Set up logger
logger = get_app_logger(__name__)

def run_model_training(
    features_path: str = 'data/processed/features.csv',
    model_output_dir: str = 'models',
    test_size: float = 0.2,
    time_split: bool = True,
    random_state: int = 42,
    version: str = None,
    register: bool = True,
    promote_to_production: bool = False
) -> Dict:
    """Run the model training pipeline"""
    # Load features
    features_df = load_df(features_path)
    
    # Split features and target
    if 'target' not in features_df.columns:
        raise ValueError("Target column 'target' not found in features")
    
    X = features_df.drop('target', axis=1)
    y = features_df['target']
    
    # Identify categorical and numerical features
    categorical_features = [col for col in X.columns if col.startswith('issuer_')]
    numerical_features = [col for col in X.columns if not col.startswith('issuer_') 
                         and col not in ['asof_date', 'data_source', 'issuer', 'news_text']]
    
    # Initialize and train model
    model = CreditScoreModel(random_state=random_state)
    results = model.train(
        X=X,
        y=y,
        categorical_features=categorical_features,
        numerical_features=numerical_features,
        test_size=test_size,
        time_split=time_split
    )
    
    # Generate and save model explanations
    explanation = model.explain(results["X_test"])
    
    # Save training artifacts and register model
    model_path, model_id = save_training_artifacts(
        model, 
        results, 
        output_dir=model_output_dir,
        version=version,
        register=register
    )
    
    # Print metrics
    logger.info("Model training complete")
    logger.info(f"ROC-AUC: {results['metrics']['roc_auc']:.4f}")
    logger.info(f"PR-AUC: {results['metrics']['pr_auc']:.4f}")
    logger.info(f"Brier score: {results['metrics']['brier']:.4f}")
    logger.info(f"K-S statistic: {results['metrics']['ks']:.4f}")
    
    # Promote to production if requested
    if promote_to_production and model_id:
        registry = ModelRegistry()
        success = registry.promote_to_production(model_id)
        if success:
            logger.info(f"Model {model_id} promoted to production")
        else:
            logger.warning(f"Failed to promote model {model_id} to production")
    
    return {
        "model": model,
        "results": results,
        "explanation": explanation,
        "model_path": model_path,
        "model_id": model_id
    }

def create_experiment(
    name: str,
    model_variants: Dict[str, float],
    description: str = ""
) -> str:
    """Create an A/B testing experiment
    
    Args:
        name: Name of the experiment
        model_variants: Dictionary mapping model IDs to traffic percentages
        description: Description of the experiment
        
    Returns:
        experiment_id: ID of the created experiment
    """
    registry = ModelRegistry()
    experiment_id = registry.create_experiment(
        name=name,
        model_variants=model_variants,
        description=description
    )
    
    if experiment_id:
        logger.info(f"Created experiment {name} with ID {experiment_id}")
    else:
        logger.error(f"Failed to create experiment {name}")
    
    return experiment_id


def list_models() -> None:
    """List all models in the registry"""
    registry = ModelRegistry()
    models = registry.list_models()
    
    if not models:
        logger.info("No models found in registry")
        return
    
    logger.info(f"Found {len(models)} models in registry:")
    for model in models:
        status = model.get("status", "unknown")
        status_marker = "*" if status == "production" else " "
        logger.info(f"{status_marker} {model['id']}: {model['name']} v{model['version']} - {model['description']}")
        logger.info(f"    ROC-AUC: {model['metrics'].get('roc_auc', 'N/A'):.4f}")


def list_experiments() -> None:
    """List all experiments in the registry"""
    registry = ModelRegistry()
    experiments = registry.list_experiments()
    
    if not experiments:
        logger.info("No experiments found in registry")
        return
    
    logger.info(f"Found {len(experiments)} experiments in registry:")
    for exp in experiments:
        logger.info(f"{exp['id']}: {exp['name']} - {exp['status']}")
        logger.info(f"    Description: {exp['description']}")
        logger.info(f"    Model variants: {exp['model_variants']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CredTech XScore Model Training and Management")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Train model command
    train_parser = subparsers.add_parser("train", help="Train a new model")
    train_parser.add_argument("--features", type=str, default="data/processed/features.csv", help="Path to features CSV")
    train_parser.add_argument("--output-dir", type=str, default="models", help="Output directory for model artifacts")
    train_parser.add_argument("--test-size", type=float, default=0.2, help="Test set size")
    train_parser.add_argument("--time-split", action="store_true", help="Use time-based split")
    train_parser.add_argument("--random-state", type=int, default=42, help="Random state for reproducibility")
    train_parser.add_argument("--version", type=str, help="Model version")
    train_parser.add_argument("--no-register", action="store_true", help="Don't register model in registry")
    train_parser.add_argument("--promote", action="store_true", help="Promote model to production")
    
    # List models command
    list_models_parser = subparsers.add_parser("list-models", help="List all models in registry")
    
    # List experiments command
    list_experiments_parser = subparsers.add_parser("list-experiments", help="List all experiments in registry")
    
    # Create experiment command
    create_experiment_parser = subparsers.add_parser("create-experiment", help="Create an A/B testing experiment")
    create_experiment_parser.add_argument("--name", type=str, required=True, help="Experiment name")
    create_experiment_parser.add_argument("--description", type=str, default="", help="Experiment description")
    create_experiment_parser.add_argument("--model-variants", type=str, required=True, 
                                         help="Model variants as 'model_id:percentage,model_id:percentage'")
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "train":
        run_model_training(
            features_path=args.features,
            model_output_dir=args.output_dir,
            test_size=args.test_size,
            time_split=args.time_split,
            random_state=args.random_state,
            version=args.version,
            register=not args.no_register,
            promote_to_production=args.promote
        )
    elif args.command == "list-models":
        list_models()
    elif args.command == "list-experiments":
        list_experiments()
    elif args.command == "create-experiment":
        # Parse model variants
        model_variants = {}
        for variant in args.model_variants.split(","):
            model_id, percentage = variant.split(":")
            model_variants[model_id] = float(percentage)
        
        create_experiment(
            name=args.name,
            model_variants=model_variants,
            description=args.description
        )
    else:
        parser.print_help()