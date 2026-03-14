.PHONY: help dev prod build up down logs clean install test lint format

help:
	@echo "Solen AI Intelligence Platform - Makefile Commands"
	@echo "=================================================="
	@echo "make dev              - Start services in development mode"
	@echo "make prod             - Start services in production mode"
	@echo "make build            - Build Docker images"
	@echo "make up               - Start Docker containers"
	@echo "make down             - Stop Docker containers"
	@echo "make logs             - View container logs"
	@echo "make clean            - Clean up containers and images"
	@echo "make install          - Install all dependencies"
	@echo "make test             - Run backend tests"
	@echo "make lint             - Run linting"
	@echo "make format           - Format code"
	@echo "make backend-dev      - Run backend in development"
	@echo "make frontend-dev     - Run frontend in development"
	@echo "make mcp-dev          - Run MCP server in development"

dev:
	docker-compose -f docker-compose.yml up --build

prod:
	docker-compose -f docker-compose.prod.yml up -d

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down --volumes --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +

install:
	cd backend && pip install -r requirements.txt
	cd mcp_server && pip install -r requirements.txt
	cd frontend && npm install

test:
	cd backend && pytest tests/ -v --cov=. --cov-report=html

lint:
	cd backend && pylint agents/ backend/ mcp_server/ --disable=C0111,C0103 || true

format:
	cd backend && black agents/ backend/ mcp_server/ --line-length=100
	cd backend && isort agents/ backend/ mcp_server/

backend-dev:
	cd backend && uvicorn main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev

mcp-dev:
	cd mcp_server && python server.py

seed-db:
	cd backend && python -c "from database import init_db; init_db()"

.DEFAULT_GOAL := help
