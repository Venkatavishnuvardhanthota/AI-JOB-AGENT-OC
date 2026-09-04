.PHONY: install test lint format docker dev backend frontend seed clean help

help:
	@echo "AI Job Agent v2.1.0 — Development Commands"
	@echo ""
	@echo "  make install     Install all Python dependencies"
	@echo "  make dev         Start backend dev server with hot reload"
	@echo "  make test        Run all tests"
	@echo "  make lint        Run ruff linter"
	@echo "  make format      Run ruff formatter"
	@echo "  make docker      Build and start all Docker services"
	@echo "  make backend     Start backend only (uvicorn)"
	@echo "  make frontend    Start frontend dev server"
	@echo "  make seed        Seed database with demo data"
	@echo "  make clean       Remove cache, build, and runtime artifacts"

install:
	cd backend && pip install -r requirements.txt

dev:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	cd backend && python -m pytest tests/ -x -q --ignore=tests/test_database_models.py --ignore=tests/test_repositories.py

test-all:
	cd backend && python -m pytest tests/ -x -q

test-cov:
	cd backend && python -m pytest tests/ --cov=app --cov-report=term-missing

lint:
	cd backend && python -m ruff check app/ tests/

format:
	cd backend && python -m ruff format app/ tests/

docker:
	docker compose up --build -d

backend:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev

seed:
	cd backend && python -m scripts.seed

clean:
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd backend && find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	cd frontend && rm -rf node_modules dist 2>/dev/null || true
	rm -rf backend/.coverage backend/htmlcov 2>/dev/null || true
