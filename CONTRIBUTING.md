# Contributing to CredTech XScore

Thank you for your interest in contributing to CredTech XScore! This document provides guidelines and workflows for contributing to the project.

## Development Workflow

### Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/credtech-xscore.git
   cd credtech-xscore
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt  # If available
   ```

### Branch Strategy

We follow a simplified Git workflow:

- `main`: Production-ready code
- `develop`: Integration branch for feature development
- `feature/*`: Feature branches for new functionality
- `bugfix/*`: Bug fix branches
- `release/*`: Release preparation branches

### Development Process

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the code style guidelines
   - Add appropriate tests
   - Update documentation as needed

3. **Run tests locally**
   ```bash
   pytest
   ```

4. **Format and lint your code**
   ```bash
   black .
   flake8
   isort .
   ```

5. **Commit your changes**
   ```bash
   git commit -m "feat: add your feature description"
   ```
   We follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

6. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a pull request**
   - Provide a clear description of the changes
   - Link to any relevant issues
   - Request reviews from team members

## Extending the Project

### Adding New Data Sources

1. Create a new data source class in `src/ingest/`
2. Implement the required interface methods:
   - `__init__(self, name, **kwargs)`
   - `load_data(self) -> pd.DataFrame`
3. Register your data source in `src/ingest/main.py`

### Adding New Features

1. Update the `FeatureProcessor` class in `src/features/processor.py`
2. Add your feature extraction logic
3. Update tests in `tests/test_feature_processor.py`
4. Document your features in the code and README

### Modifying the Model

1. Update the model parameters in `src/utils/config.py`
2. Modify the `CreditScoreModel` class in `src/model/trainer.py` as needed
3. Update tests in `tests/test_credit_score_model.py`
4. Document changes in `model_card.md`

### Enhancing the Streamlit App

1. Modify `src/serve/app.py`
2. Test the app locally with `streamlit run src/serve/app.py`
3. Ensure Docker compatibility

## Code Style Guidelines

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all functions, classes, and modules
- Keep functions focused on a single responsibility
- Use meaningful variable and function names

## Testing Guidelines

- Write unit tests for all new functionality
- Ensure tests are deterministic (use fixed random seeds)
- Mock external dependencies in tests
- Aim for high test coverage, especially for critical components

## Documentation Guidelines

- Update README.md with any user-facing changes
- Keep model_card.md up to date with model changes
- Document API changes in docstrings
- Add comments for complex code sections

## Release Process

1. Update version numbers in relevant files
2. Update CHANGELOG.md with notable changes
3. Create a release branch: `release/vX.Y.Z`
4. Run final tests and quality checks
5. Merge to main and tag the release
6. Update the develop branch with the release

## Questions and Support

If you have questions or need support, please:

1. Check existing issues and documentation
2. Create a new issue with a clear description
3. Tag appropriate team members

Thank you for contributing to CredTech XScore!