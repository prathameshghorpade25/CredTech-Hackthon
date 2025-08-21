# Model Versioning and A/B Testing Guide

## Overview

This guide explains how to use the model versioning and A/B testing capabilities in the CredTech XScore system. These features allow you to:

- Register and track multiple model versions
- Promote specific models to production
- Create A/B testing experiments to compare model performance
- Monitor model performance metrics

## Model Registry

The Model Registry is a central repository for managing model versions. It stores model artifacts, metadata, and performance metrics.

### Key Concepts

- **Model ID**: A unique identifier for each model version
- **Model Version**: A version string that identifies a specific model iteration
- **Production Model**: The currently active model used for production predictions
- **Model Status**: The current state of a model (e.g., "active", "archived")

## Using the Model Manager CLI

The `model_manager_cli.py` script provides a command-line interface for managing models and experiments.

### Training a New Model Version

```bash
python scripts/model_manager_cli.py train --version "v1.2.0" --register --promote --description "Improved model with additional features"
```

Options:
- `--version`: Version identifier for the model (optional, will generate timestamp-based version if not provided)
- `--register`: Register the model in the registry
- `--promote`: Promote the model to production
- `--description`: Description of the model

### Listing Models

```bash
python scripts/model_manager_cli.py list-models
```

Add `--json` for JSON output format.

### Getting Model Information

```bash
python scripts/model_manager_cli.py get-model <model_id>
```

Add `--json` for JSON output format.

### Promoting a Model to Production

```bash
python scripts/model_manager_cli.py promote <model_id>
```

## A/B Testing

A/B testing allows you to compare the performance of different model versions by routing a percentage of traffic to each model.

### Creating an Experiment

```bash
python scripts/model_manager_cli.py create-experiment "New Features Test" \
  --description "Testing impact of new features" \
  --model-ids "model_v1,model_v2" \
  --traffic-split "80,20"
```

Options:
- `name`: Name of the experiment
- `--description`: Description of the experiment
- `--model-ids`: Comma-separated list of model IDs to include in the experiment
- `--traffic-split`: Comma-separated list of traffic percentages for each model (must sum to 100)

### Listing Experiments

```bash
python scripts/model_manager_cli.py list-experiments
```

Add `--json` for JSON output format.

### Getting Experiment Information

```bash
python scripts/model_manager_cli.py get-experiment <experiment_id>
```

Add `--json` for JSON output format.

### Stopping an Experiment

```bash
python scripts/model_manager_cli.py stop-experiment <experiment_id>
```

## API Integration

The API has been updated to support model versioning and A/B testing.

### Endpoints

- `GET /api/models`: List all available models
- `GET /api/experiments`: List all A/B testing experiments
- `GET /api/model-info?model_id=<model_id>`: Get information about a specific model
- `POST /api/score?model_id=<model_id>`: Score using a specific model
- `POST /api/batch-score?model_id=<model_id>`: Batch score using a specific model

If no `model_id` is provided, the system will use A/B testing or the production model.

## Implementation Details

### Model Registry Structure

The Model Registry stores models in the following structure:

```
models/
  registry/
    models/
      <model_id>/
        model.joblib
        metadata.json
        metrics.json
        plots/
          calibration_curve.png
          roc_curve.png
          pr_curve.png
    experiments/
      <experiment_id>/
        metadata.json
        results.json
    registry.json
```

### Model Versioning

When training a new model, you can specify a version or let the system generate one based on the current timestamp. The model is saved with this version and can be registered in the registry.

### A/B Testing

A/B testing works by routing a percentage of traffic to different model versions based on the experiment configuration. The system uses a deterministic routing mechanism based on the request ID to ensure consistent model assignment for the same request.

## Best Practices

1. **Version Naming**: Use semantic versioning (e.g., "v1.2.3") for model versions
2. **Model Description**: Include information about model changes, features, and training parameters
3. **Gradual Rollout**: Start with a small percentage of traffic when testing new models
4. **Monitoring**: Regularly check model performance metrics during experiments
5. **Documentation**: Document model changes and experiment results

## Troubleshooting

### Common Issues

- **Model Not Found**: Ensure the model ID is correct and the model exists in the registry
- **Experiment Creation Failed**: Check that model IDs exist and traffic percentages sum to 100
- **Model Loading Failed**: Verify that model files are not corrupted

### Logs

Check the application logs for detailed error messages:

```
tail -f logs/credtech_xscore.log
```

## Conclusion

The model versioning and A/B testing system provides a robust framework for managing model lifecycle and experimentation. By following this guide, you can effectively manage multiple model versions, conduct experiments, and make data-driven decisions about model deployment.