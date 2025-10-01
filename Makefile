.PHONY: help install seed test up down train eval fmt lint clean deploy-azure

# Default target
help:
	@echo "Available commands:"
	@echo "  install       - Install dependencies"
	@echo "  seed          - Generate sample data and seed database"
	@echo "  train         - Train ML models"
	@echo "  eval          - Run model evaluations"
	@echo "  test          - Run all tests"
	@echo "  up            - Start local development environment"
	@echo "  down          - Stop local development environment"
	@echo "  fmt           - Format code with black and ruff"
	@echo "  lint          - Lint code with ruff"
	@echo "  clean         - Clean up temporary files"
	@echo "  deploy-azure  - Deploy to Azure Container Apps"

# Development setup
install:
	pip install -r requirements.txt
	pip install -e .

# Data and model setup
seed:
	python scripts/generate_synth_data.py
	python scripts/seed_db.py
	python rag/index.py

# Model training and evaluation
train:
	python ai/model_train.py --data seed_data/sample_sensors.csv --output ai/artifacts

eval:
	python ai/evals.py --data seed_data/sample_sensors.csv --artifacts ai/artifacts

# Testing
test:
	pytest tests/ -v --cov=api --cov=ai --cov=rag --cov-report=html

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# Local development
up:
	docker compose up --build -d
	@echo "Services starting..."
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Prometheus: http://localhost:9000"

down:
	docker compose down -v

logs:
	docker compose logs -f

# Code quality
fmt:
	ruff format .
	black .

lint:
	ruff check .
	mypy api/ ai/ rag/ --ignore-missing-imports

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf temp_uploads/
	rm -rf ai/artifacts/*.joblib
	rm -rf rag/faiss.index
	rm -rf rag/chunks.pkl

# Azure deployment
deploy-azure:
	./infra/azure-deploy.sh

# Database operations
db-migrate:
	alembic upgrade head

db-rollback:
	alembic downgrade -1

db-reset:
	alembic downgrade base
	alembic upgrade head

# Worker operations
worker-start:
	python workers/scheduler.py

worker-queue:
	python -m rq worker --url redis://localhost:6379/0

# Monitoring
metrics:
	@echo "Prometheus metrics available at http://localhost:9000/metrics"

# Quick development cycle
dev-setup: install seed train
	@echo "Development environment ready!"

# Production build
build:
	docker build -f infra/docker/Dockerfile.api -t pdm-api:latest .
	docker build -f infra/docker/Dockerfile.worker -t pdm-worker:latest .

# Health checks
health:
	curl -f http://localhost:8000/healthz || echo "API not responding"
	curl -f http://localhost:9000/metrics || echo "Prometheus not responding"



