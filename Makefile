# CredTech XScore Makefile

.PHONY: run test docker clean lint format help

# Default target
help:
	@echo "CredTech XScore Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make run        Run the full pipeline"
	@echo "  make app        Run the Streamlit app"
	@echo "  make test       Run tests"
	@echo "  make docker     Build Docker image"
	@echo "  make docker-run Run Docker container"
	@echo "  make clean      Clean generated files"
	@echo "  make lint       Run linting"
	@echo "  make format     Format code"
	@echo "  make help       Show this help message"

# Run the full pipeline
run:
	@echo "Running CredTech XScore pipeline..."
	python run_all.py

# Run the Streamlit app
app:
	@echo "Starting Streamlit app..."
	streamlit run src/serve/app.py

# Run tests
test:
	@echo "Running tests..."
	pytest -v

# Run tests with coverage
test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=src tests/

# Build Docker image
docker:
	@echo "Building Docker image..."
	docker build -t credtech-xscore .

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	docker-compose up

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

# Run linting
lint:
	@echo "Running linting..."
	flake8 src tests

# Format code
format:
	@echo "Formatting code..."
	black src tests
	isort src tests