# CredTech XScore

An explainable, reproducible credit scoring pipeline for the CredTech Hackathon.

## Problem Statement

Credit risk assessment traditionally relies on limited financial data and lacks transparency in decision-making. CredTech XScore addresses these challenges by:

1. Combining structured financial data with unstructured news sentiment data
2. Providing explainable predictions with reason codes
3. Delivering a reproducible, production-ready pipeline
4. Offering an interactive visualization tool for risk managers

## Overview

CredTech XScore is a credit scoring system that combines structured financial data with unstructured news data to predict credit risk. The system provides explainable predictions using SHAP values, allowing users to understand the factors influencing each score.

### Architecture

![Architecture Diagram](reports/figures/architecture.png)

The pipeline consists of four main components:

1. **Data Ingestion**: Collects and processes structured financial data and unstructured news data
2. **Feature Engineering**: Transforms raw data into meaningful features, including short-term and long-term signals
3. **Model Training**: Trains a LightGBM classifier with cross-validation and calibration
4. **Serving**: Provides predictions and explanations through a Streamlit app

## Features

- Data ingestion from multiple sources (structured and unstructured)
- Feature engineering pipeline
- Model training with explainability (SHAP)
- Comprehensive metrics (ROC-AUC, PR-AUC, Brier score, K-S)
- Model versioning and A/B testing capabilities
- Interactive Streamlit demo app
- Fully reproducible pipeline

## Project Structure

```
├── data/
│   ├── processed/      # Processed data files
│   └── raw/            # Raw input data
├── models/             # Trained model artifacts
│   └── registry/       # Model registry for versioning
├── notebooks/          # Jupyter notebooks (if any)
├── reports/
│   └── figures/        # Generated plots and visualizations
├── src/
│   ├── ingest/         # Data ingestion modules
│   ├── features/       # Feature engineering
│   ├── model/          # Model training and evaluation
│   │   └── registry.py # Model registry implementation
│   ├── serve/          # Serving and demo app
│   │   └── model_manager.py # Model versioning and A/B testing
│   └── utils/          # Utility functions
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── model_card.md       # Model documentation
├── requirements.txt    # Python dependencies
└── run_all.py          # Main pipeline script
```

## Installation

### Using Docker (Recommended)

```bash
# Build and run the pipeline
docker-compose up pipeline

# Run the Streamlit demo app
docker-compose up streamlit
```

The Streamlit app will be available at http://localhost:8501

### Local Installation

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python run_all.py

# Run the Streamlit app
streamlit run src/serve/app.py
```

## Usage

### Running the Pipeline

The `run_all.py` script orchestrates the full pipeline:

```bash
python run_all.py [options]
```

### Model Versioning and A/B Testing

CredTech XScore now supports model versioning and A/B testing capabilities. Use the model manager CLI to manage models and experiments:

```bash
# Train a new model version
python scripts/model_manager_cli.py train --version "v1.0.0" --register --promote

# List all registered models
python scripts/model_manager_cli.py list-models

# Create an A/B testing experiment
python scripts/model_manager_cli.py create-experiment "Test Experiment" --model-ids "model1,model2" --traffic-split "50,50"
```

For more details, see the [Model Versioning Guide](docs/model_versioning_guide.md).

Options:
- `--skip-ingestion`: Skip data ingestion step
- `--skip-features`: Skip feature engineering step
- `--skip-training`: Skip model training step
- `--test-size`: Test set size (default: 0.2)
- `--random-state`: Random seed (default: 42)

### Using the Streamlit App

The Streamlit app provides an interactive interface to explore the model:

```bash
streamlit run src/serve/app.py
```

## Model

The credit scoring model is a LightGBM classifier trained on financial and news sentiment data. It provides explainable predictions using SHAP values.

For detailed information about the model, see the [Model Card](model_card.md).

## License

This project is for the CredTech Hackathon and is not licensed for production use.






