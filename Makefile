SHELL := /bin/bash
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "")
.PHONY: help test lint check build dev-setup dev-up dev-down dev-logs dev-status backup restore clean privacy-check
help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
dev-setup: ## One-click setup
	@if [ ! -d "geoflow-src" ]; then git clone --depth=1 https://github.com/yaojingang/GEOFlow.git geoflow-src; fi
	@if [ ! -f ".env" ]; then cp .env.example .env; echo "Edit .env to set AI_API_KEY"; fi
	@echo "Run 'make dev-up' to start."
dev-up: ## Start services
	docker compose up -d
	@echo "GEOEngine at http://localhost:18080/geo_admin"
dev-down: ## Stop services
	docker compose down
dev-logs: ## Follow logs
	docker compose logs -f
dev-status: ## Service status
	docker compose ps
backup: ## Backup database
	@mkdir -p backups
	docker compose exec -T postgres pg_dump -U geo_user geo_flow > backups/geoflow_$$(date +%Y%m%d_%H%M%S).sql
restore: ## Restore database (usage: make restore FILE=backup.sql)
	docker compose exec -T postgres psql -U geo_user -d geo_flow < $(FILE)
privacy-check: ## Privacy scan
	$(PYTHON) ../scripts/privacy-check.py .
check: ## Verify required files
	@errors=0; for f in Makefile LICENSE README.md ARCHITECTURE.md .env.example docker-compose.yml scripts/setup.sh scripts/setup.ps1; do [ ! -f "$$f" ] && echo "Missing: $$f" && errors=$$((errors+1)); done; [ $$errors -eq 0 ] && echo "All files OK" || exit 1
test: check
clean: ## Clean temp files
	rm -rf backups/ docker-data/
