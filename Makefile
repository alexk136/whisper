# Makefile for Whisper Microservice

.PHONY: help build up down logs test clean deploy lint format install dev prod stop restart status health

# Default target
help: ## Show this help message
	@echo "Whisper Microservice Management"
	@echo "Usage: make [target]"
	@echo ""
	@echo "🚀 For new developers: make quick-start"
	@echo "📋 Available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development targets
dev: ## Start development environment
	docker-compose up -d
	@echo "🚀 Development environment started"
	@echo "API available at: http://localhost:8000"
	@echo "View logs with: make logs"

build: ## Build Docker images
	docker-compose build

up: ## Start services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

stop: ## Stop services without removing containers
	docker-compose stop

restart: ## Restart services
	docker-compose restart

logs: ## Show service logs
	docker-compose logs -f --tail=100

status: ## Show service status
	docker-compose ps

health: ## Check service health
	@echo "🏥 Checking service health..."
	@curl -f http://localhost:8000/health || echo "❌ Service is not healthy"
	@echo "✅ Health check completed"

# Production targets
prod: ## Start production environment
	docker-compose -f docker-compose.prod.yml up -d
	@echo "🚀 Production environment started"

prod-build: ## Build production images
	docker-compose -f docker-compose.prod.yml build

prod-down: ## Stop production environment
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## Show production logs
	docker-compose -f docker-compose.prod.yml logs -f --tail=100

prod-status: ## Show production service status
	docker-compose -f docker-compose.prod.yml ps

# Testing targets
test: ## Run all tests
	python -m pytest tests/ -v

test-unit: ## Run unit tests only
	python -m pytest tests/test_hybrid_*.py -v

test-api: ## Run API tests
	python -m pytest tests/test_hybrid_api.py -v

test-cli: ## Run CLI tests
	python -m pytest cli_tests/ -v

test-coverage: ## Run tests with coverage
	python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# Code quality targets
lint: ## Run linting
	@echo "🔍 Running linting..."
	black --check app/ tests/ cli_tests/
	flake8 app/ tests/ cli_tests/
	isort --check-only app/ tests/ cli_tests/

format: ## Format code
	@echo "🎨 Formatting code..."
	black app/ tests/ cli_tests/
	isort app/ tests/ cli_tests/
	@echo "✅ Code formatted"

# Installation targets
install: ## Install dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black flake8 isort

setup: ## Initial project setup (creates venv, installs deps, creates dirs)
	@echo "🚀 Running initial project setup..."
	chmod +x setup.sh
	./setup.sh
	@echo "✅ Setup completed"

# Deployment targets
deploy: ## Deploy using deployment script
	@echo "🚀 Starting deployment..."
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh production

deploy-staging: ## Deploy to staging
	@echo "🚀 Starting staging deployment..."
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh staging

# Cleanup targets
clean: ## Clean up containers and images
	@echo "🧹 Cleaning up..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup completed"

clean-all: ## Clean everything including volumes
	@echo "🧹 Deep cleaning..."
	docker-compose down -v --remove-orphans
	docker system prune -af --volumes
	@echo "✅ Deep cleanup completed"

# Backup targets
backup: ## Create backup
	@echo "📦 Creating backup..."
	mkdir -p backups
	tar -czf "backups/whisper-backup-$(shell date +%Y%m%d_%H%M%S).tar.gz" \
		storage/ logs/ models/ data/ .env config.yaml
	@echo "✅ Backup created in backups/"

# Monitoring targets
monitor: ## Start monitoring stack
	docker-compose --profile monitoring up -d
	@echo "📊 Monitoring started at http://localhost:9100"

monitor-down: ## Stop monitoring
	docker-compose --profile monitoring down

# Database targets (if using database)
db-migrate: ## Run database migrations
	@echo "📊 Running migrations..."
	# Add your migration commands here

db-backup: ## Backup database
	@echo "📦 Backing up database..."
	# Add your database backup commands here

# Git workflow helpers
git-feature: ## Create new feature branch (usage: make git-feature BRANCH=feature-name)
	@if [ -z "$(BRANCH)" ]; then \
		echo "❌ Please provide branch name: make git-feature BRANCH=your-feature-name"; \
		exit 1; \
	fi
	git checkout -b feature/$(BRANCH)
	@echo "✅ Created and switched to feature/$(BRANCH)"

git-finish: ## Finish feature branch (commit and push)
	@if [ $$(git symbolic-ref --short HEAD | grep -c "feature/") -eq 0 ]; then \
		echo "❌ Not on a feature branch"; \
		exit 1; \
	fi
	git add .
	git status
	@echo "📝 Ready to commit. Run: git commit -m 'your message' && git push origin HEAD"

# SSL/TLS targets (if needed)
ssl-generate: ## Generate SSL certificates
	@echo "🔐 Generating SSL certificates..."
	mkdir -p ssl
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout ssl/whisper.key \
		-out ssl/whisper.crt \
		-subj "/C=US/ST=State/L=City/O=Organization/CN=whisper-api"
	@echo "✅ SSL certificates generated in ssl/"

# Quick helpers
quick-start: setup build dev ## Quick start for new developers

quick-test: format lint test ## Quick test pipeline

quick-deploy: test deploy ## Quick deploy after testing

# System information
info: ## Show system information
	@echo "📋 System Information"
	@echo "===================="
	@echo "Docker version: $$(docker --version)"
	@echo "Docker Compose version: $$(docker-compose --version)"
	@echo "Python version: $$(python --version)"
	@echo "Current branch: $$(git symbolic-ref --short HEAD)"
	@echo "Last commit: $$(git log -1 --oneline)"
	@echo "Working directory: $$(pwd)"
	@echo "Available disk space: $$(df -h . | tail -1 | awk '{print $$4}')"

# Performance testing
perf-test: ## Run performance tests
	@echo "⚡ Running performance tests..."
	# Add your performance testing commands here
	@echo "🔧 Performance tests not implemented yet"

# Security scanning
security-scan: ## Run security scan
	@echo "🔒 Running security scan..."
	# Add your security scanning commands here
	@echo "🔧 Security scan not implemented yet"
