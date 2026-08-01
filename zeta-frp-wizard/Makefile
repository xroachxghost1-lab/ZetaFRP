# ================================================================
# Zeta FRP Wizard — Makefile
#
# ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
# Unauthorised use, distribution, or reproduction is an act of war.
# Copyright © 2026 Zeta Omniverse. All rights reserved.
# ================================================================

.PHONY: help install test lint clean build run

help:
	@echo "Zeta FRP Wizard — Development Commands"
	@echo ""
	@echo "  make install    Install dependencies"
	@echo "  make test       Run test suite"
	@echo "  make lint       Run code quality checks"
	@echo "  make build      Build standalone executable"
	@echo "  make run        Launch the wizard"
	@echo "  make clean      Remove build artifacts"
	@echo "  make update-db  Update SPL method database"

install:
	pip install -r requirements.txt
	pip install -e .

test:
	python -m pytest tests/ -v --cov=zeta_frp --cov-report=term

lint:
	@echo "Running lint checks..."
	@python -m flake8 zeta_frp/ --max-line-length=120 --ignore=E501,W503 2>/dev/null || echo "flake8 not installed. Run: pip install flake8"

build:
	@echo "Building standalone executable..."
	@python -m PyInstaller zeta_frp/main.py --onefile --windowed --name "Zeta-FRP-Wizard"

run:
	python -m zeta_frp.main

update-db:
	python scripts/update_spl_db.py

clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf __pycache__/ .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
