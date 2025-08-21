# Model Card: CredTech XScore

## Model Details

- **Model Name**: CredTech XScore
- **Version**: 1.0.0
- **Type**: Gradient Boosting Classifier (LightGBM)
- **Date**: June 2024
- **License**: For CredTech Hackathon Use
- **Developers**: CredTech Hackathon Team

## Intended Use

- **Primary Use**: Credit risk assessment and scoring for financial institutions
- **Intended Users**: Financial analysts, credit risk managers, loan officers
- **Use Cases**:
  - Evaluating creditworthiness of corporate issuers
  - Monitoring changes in credit risk over time
  - Identifying early warning signals from financial and news data
  - Supporting credit approval and review processes
- **Out-of-Scope Uses**: 
  - Not intended for automated lending decisions without human oversight
  - Not for use in regulated lending without additional compliance review
  - Not suitable for consumer credit scoring
  - Not designed for real-time transaction approval

## Training Data

- **Sources**: 
  - Structured financial data (transaction history, balances, income)
  - News sentiment data (processed using VADER sentiment analysis)
- **Data Split**: Time-based split (80% train, 20% test)

## Model Parameters

- **Algorithm**: LightGBM Classifier
- **Hyperparameters**:
  - n_estimators: 100
  - learning_rate: 0.1
  - max_depth: 5
  - early_stopping_rounds: 10
- **Feature Preprocessing**: 
  - Numerical features: StandardScaler
  - Categorical features: One-hot encoding

## Evaluation Results

- **Metrics**:
  - ROC-AUC: Measures discrimination ability (higher is better)
  - PR-AUC: Measures precision-recall trade-off (higher is better)
  - Brier Score: Measures calibration quality (lower is better)
  - K-S Statistic: Measures separation between good and bad cases (higher is better)

## Ethical Considerations

- **Fairness**: 
  - Model has not been comprehensively tested for bias across protected attributes
  - Potential for disparate impact on different industry sectors should be evaluated
  - Regular fairness audits should be conducted if deployed in production
  - Monitoring for emergent biases should be implemented

- **Privacy**: 
  - Model does not use personally identifiable information directly
  - All data should be anonymized before processing
  - Data retention policies should be established and followed

- **Transparency**: 
  - SHAP values provide feature-level explanations for each prediction
  - Plain-language reason codes are provided for key factors
  - Model decisions can be audited and explained to stakeholders
  - Documentation is provided for all model components

- **Risks**:
  - Over-reliance on model predictions without human judgment
  - Potential for feedback loops if model decisions affect future data
  - News sentiment analysis may be affected by media bias
  - Model may not perform well during economic shocks or black swan events

## Limitations

- **Data Limitations**: 
  - Limited sample size in training data
  - Simulated news data for demonstration purposes
  - No real-time data integration
  - Training data may not represent all market conditions, especially extreme events
  - Limited historical data for some issuers or sectors
  - News sentiment analysis may be affected by source bias or coverage gaps
  - Data freshness depends on update frequency of underlying sources
- **Model Limitations**:
  - Does not account for macroeconomic factors
  - Limited to features available in the training data
  - No handling of concept drift over time
  - May not capture complex non-linear relationships between some features
  - Performance may degrade during market stress or regime changes
  - Limited ability to incorporate qualitative factors not represented in data
  - Calibration may drift over time requiring regular retraining

## Explainability

- **Method**: SHAP (SHapley Additive exPlanations)
- **Implementation**: TreeExplainer from SHAP library
- **Output**: 
  - Feature contributions to individual predictions
  - Plain-language reason codes for key factors
  - Per-issuer explanation JSON files
  - Calibration, ROC, and PR curves

## Retraining Plan

- **Frequency**: Quarterly retraining recommended
- **Triggers**: 
  - Significant performance degradation (>5% drop in AUC)
  - Major market events or economic shifts
  - Addition of new data sources or features
  - Drift detection in feature distributions
- **Process**:
  - Collect new labeled data
  - Evaluate model performance on new data
  - Retrain with combined historical and new data
  - Validate performance improvements
  - Update model artifacts and documentation
- **Versioning**: 
  - Major version increments for architecture changes
  - Minor version increments for retraining with new data
  - Patch version for bug fixes or small improvements

## Deployment

- **Requirements**: 
  - Python 3.8+
  - Dependencies in requirements.txt
  - Docker for containerized deployment
- **Compute**: 
  - CPU sufficient, no GPU required
  - Minimum 4GB RAM recommended
  - Storage for model artifacts (~100MB)
- **Serving**: 
  - Streamlit app for visualization and exploration
  - FastAPI for potential API endpoints
  - Docker containers for reproducible deployment
- **Monitoring**:
  - Logging of predictions and explanations
  - Performance metrics tracking
  - Data drift detection recommended
  - Regular model evaluation against new data
- **Inference Time**: < 100ms per prediction

## Reproducibility

- **Random Seed**: 42
- **Environment**: Docker container with Python 3.11
- **Pipeline**: Fully reproducible via run_all.py script






