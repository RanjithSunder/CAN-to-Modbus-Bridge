.PHONY: help install run test clean build docker-build docker-run lint format

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies"
	@echo "  run          - Run the bridge application"
	@echo "  test         - Run tests (placeholder)"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Run the application
run:
	python main.py

# Placeholder for tests
test:
	@echo "Tests not implemented yet"
	# python -m pytest tests/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build package
build: clean
	python setup.py sdist bdist_wheel

# Docker operations
docker-build:
	docker build -t can-modbus-bridge .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

# Code quality
lint:
	flake8 main.py --max-line-length=120
	# pylint main.py

format:
	black main.py --line-length=120
	# isort main.py

# Development setup
dev-install:
	pip install -r requirements.txt
	pip install black flake8 pylint pytest
	pip install -e .
