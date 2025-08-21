#!/usr/bin/env python
"""Command-line interface for managing model versioning and A/B testing"""

import os
import sys
import argparse
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model.main import run_model_training, create_experiment, list_models, list_experiments
from src.model.registry import ModelRegistry


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="CredTech XScore Model Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Train model command
    train_parser = subparsers.add_parser("train", help="Train a new model version")
    train_parser.add_argument("--version", type=str, help="Version identifier for the model")
    train_parser.add_argument("--register", action="store_true", help="Register the model in the registry")
    train_parser.add_argument("--promote", action="store_true", help="Promote the model to production")
    train_parser.add_argument("--description", type=str, default="", help="Description of the model")
    
    # List models command
    list_models_parser = subparsers.add_parser("list-models", help="List all models in the registry")
    list_models_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Get model info command
    get_model_parser = subparsers.add_parser("get-model", help="Get information about a specific model")
    get_model_parser.add_argument("model_id", type=str, help="ID of the model to get information about")
    get_model_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Promote model command
    promote_parser = subparsers.add_parser("promote", help="Promote a model to production")
    promote_parser.add_argument("model_id", type=str, help="ID of the model to promote")
    
    # Create experiment command
    experiment_parser = subparsers.add_parser("create-experiment", help="Create a new A/B testing experiment")
    experiment_parser.add_argument("name", type=str, help="Name of the experiment")
    experiment_parser.add_argument("--description", type=str, default="", help="Description of the experiment")
    experiment_parser.add_argument("--model-ids", type=str, required=True, 
                                 help="Comma-separated list of model IDs to include in the experiment")
    experiment_parser.add_argument("--traffic-split", type=str, required=True,
                                 help="Comma-separated list of traffic percentages for each model")
    
    # List experiments command
    list_exp_parser = subparsers.add_parser("list-experiments", help="List all experiments in the registry")
    list_exp_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Get experiment info command
    get_exp_parser = subparsers.add_parser("get-experiment", help="Get information about a specific experiment")
    get_exp_parser.add_argument("experiment_id", type=str, help="ID of the experiment to get information about")
    get_exp_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Stop experiment command
    stop_exp_parser = subparsers.add_parser("stop-experiment", help="Stop an active experiment")
    stop_exp_parser.add_argument("experiment_id", type=str, help="ID of the experiment to stop")
    
    return parser.parse_args()


def format_model_info(model, json_output=False):
    """Format model information for display"""
    if json_output:
        return json.dumps(model, indent=2)
    
    output = [
        f"Model ID: {model['id']}",
        f"Name: {model['name']}",
        f"Version: {model['version']}",
        f"Description: {model['description']}",
        f"Created: {model['created_at']}",
        f"Status: {model['status']}",
        f"Metrics:"
    ]
    
    for metric_name, metric_value in model['metrics'].items():
        output.append(f"  {metric_name}: {metric_value:.4f}")
    
    if model.get('is_production', False):
        output.append("Production: Yes")
    else:
        output.append("Production: No")
    
    return "\n".join(output)


def format_experiment_info(experiment, json_output=False):
    """Format experiment information for display"""
    if json_output:
        return json.dumps(experiment, indent=2)
    
    output = [
        f"Experiment ID: {experiment['id']}",
        f"Name: {experiment['name']}",
        f"Description: {experiment['description']}",
        f"Created: {experiment['created_at']}",
        f"Status: {experiment['status']}",
        f"Model Variants:"
    ]
    
    for model_id, percentage in experiment['model_variants'].items():
        output.append(f"  {model_id}: {percentage}%")
    
    return "\n".join(output)


def main():
    """Main entry point for the CLI"""
    args = parse_args()
    registry = ModelRegistry()
    
    if args.command == "train":
        print("Training new model...")
        metrics = run_model_training(
            version=args.version,
            register=args.register,
            promote_to_production=args.promote,
            description=args.description
        )
        print(f"Model training completed with ROC-AUC: {metrics['roc_auc']:.4f}")
        if args.register:
            print("Model registered in the registry")
        if args.promote:
            print("Model promoted to production")
    
    elif args.command == "list-models":
        models = list_models()
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            if not models:
                print("No models found in the registry")
            else:
                print(f"Found {len(models)} models:")
                for i, model in enumerate(models):
                    print(f"\nModel {i+1}:")
                    print(format_model_info(model))
    
    elif args.command == "get-model":
        model = registry.get_model_info(args.model_id)
        if model is None:
            print(f"Model with ID {args.model_id} not found")
            return 1
        
        print(format_model_info(model, args.json))
    
    elif args.command == "promote":
        success = registry.promote_model_to_production(args.model_id)
        if success:
            print(f"Model {args.model_id} promoted to production")
        else:
            print(f"Failed to promote model {args.model_id} to production")
            return 1
    
    elif args.command == "create-experiment":
        model_ids = args.model_ids.split(",")
        try:
            traffic_split = [float(x) for x in args.traffic_split.split(",")]
        except ValueError:
            print("Traffic split must be comma-separated list of numbers")
            return 1
        
        if len(model_ids) != len(traffic_split):
            print("Number of model IDs must match number of traffic percentages")
            return 1
        
        if sum(traffic_split) != 100:
            print("Traffic percentages must sum to 100")
            return 1
        
        # Convert to dictionary
        model_variants = {model_id: percentage for model_id, percentage in zip(model_ids, traffic_split)}
        
        experiment_id = create_experiment(
            name=args.name,
            description=args.description,
            model_variants=model_variants
        )
        
        if experiment_id:
            print(f"Experiment created with ID: {experiment_id}")
        else:
            print("Failed to create experiment")
            return 1
    
    elif args.command == "list-experiments":
        experiments = list_experiments()
        if args.json:
            print(json.dumps(experiments, indent=2))
        else:
            if not experiments:
                print("No experiments found in the registry")
            else:
                print(f"Found {len(experiments)} experiments:")
                for i, experiment in enumerate(experiments):
                    print(f"\nExperiment {i+1}:")
                    print(format_experiment_info(experiment))
    
    elif args.command == "get-experiment":
        experiment = registry.get_experiment_info(args.experiment_id)
        if experiment is None:
            print(f"Experiment with ID {args.experiment_id} not found")
            return 1
        
        print(format_experiment_info(experiment, args.json))
    
    elif args.command == "stop-experiment":
        success = registry.stop_experiment(args.experiment_id)
        if success:
            print(f"Experiment {args.experiment_id} stopped")
        else:
            print(f"Failed to stop experiment {args.experiment_id}")
            return 1
    
    else:
        print("No command specified. Use --help for usage information.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())