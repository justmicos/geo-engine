SHELL := /bin/bash
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "")
.PHONY: help test lint check build dev-setup dev-up dev-down dev-logs dev-status backup restore clean privacy-check
.PHONY: dev-up-all ai-gateway-logs evolve-run fine-tune-start fine-tune-status fine-tune-logs

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Setup
# =============================================================================
dev-setup: ## One-click setup (clone GEOFlow + create .env)
	@if [ ! -d "kengine-src" ]; then git clone --depth=1 https://github.com/justmicos/GEOFlow.git kengine-src; fi
	@if [ ! -f ".env" ]; then cp .env.example .env; echo ">>> Edit .env to set at least one AI_API_KEY"; fi
	@echo ">>> Run 'make dev-up' to start."

# =============================================================================
# Service Lifecycle
# =============================================================================
dev-up: ## Start core services (app + postgres + redis + queue + scheduler)
	docker compose up -d
	@echo ">>> GEOEngine at http://localhost:${APP_PORT:-18080}/geo_admin"

dev-up-all: ## Start ALL services including AI Gateway and fine-tuner
	docker compose --profile all up -d
	@echo ">>> GEOEngine at http://localhost:${APP_PORT:-18080}/geo_admin"
	@echo ">>> AI Gateway at http://localhost:${AI_GATEWAY_PORT:-19090}/v1"

dev-up-gateway: ## Start core + AI Gateway only
	docker compose up -d
	docker compose --profile ai-gateway up -d
	@echo ">>> AI Gateway at http://localhost:${AI_GATEWAY_PORT:-19090}/v1"

dev-down: ## Stop all services
	docker compose down
	-docker compose --profile all down

dev-logs: ## Follow all logs
	docker compose logs -f

dev-status: ## Service status
	docker compose ps

# =============================================================================
# AI Gateway
# =============================================================================
ai-gateway-logs: ## Follow AI Gateway logs
	docker compose logs -f ai-gateway

ai-gateway-test: ## Test AI Gateway chat completions endpoint
	@read -p "Model (default: deepseek-chat): " model; \
	 model=$${model:-deepseek-chat}; \
	 curl -s http://localhost:${AI_GATEWAY_PORT:-19090}/v1/chat/completions \
	   -H "Content-Type: application/json" \
	   -d "{\"model\":\"$$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with OK and the model name you are.\"}],\"temperature\":0,\"max_tokens\":20}" \
	   | python3 -m json.tool 2>/dev/null || curl -s http://localhost:${AI_GATEWAY_PORT:-19090}/v1/chat/completions \
	   -H "Content-Type: application/json" \
	   -d "{\"model\":\"$$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with OK and the model name you are.\"}],\"temperature\":0,\"max_tokens\":20}"

ai-gateway-test-embedding: ## Test AI Gateway embeddings endpoint
	curl -s http://localhost:${AI_GATEWAY_PORT:-19090}/v1/embeddings \
	  -H "Content-Type: application/json" \
	  -d "{\"model\":\"text-embedding-3-small\",\"input\":\"Hello world\"}" \
	  | python3 -m json.tool 2>/dev/null

ai-gateway-list-models: ## List available models
	curl -s http://localhost:${AI_GATEWAY_PORT:-19090}/v1/models | python3 -m json.tool 2>/dev/null

# =============================================================================
# Knowledge Evolution
# =============================================================================
evolve-run: ## Manually trigger knowledge base evolution
	@echo ">>> Triggering knowledge evolution..."
	docker compose exec -T scheduler php artisan geoflow:evolve --force
	@echo ">>> Evolution triggered. Check logs with 'make dev-logs'."

evolve-status: ## Show last evolution run status
	docker compose exec -T postgres psql -U geo_user -d geo_flow -c \
	  "SELECT id, started_at, completed_at, chunks_processed, chunks_merged, chunks_archived, status FROM evolution_runs ORDER BY id DESC LIMIT 5;"

# =============================================================================
# Fine-Tuning
# =============================================================================
fine-tune-start: ## Start fine-tuning (requires GPU + docker compose --profile fine-tune)
	docker compose --profile fine-tune up -d fine-tune
	@echo ">>> Fine-tuning container started. Monitor with 'make fine-tune-logs'."

fine-tune-status: ## Check fine-tuning status
	@if docker ps --format '{{.Names}}' | grep -q kengine-fine-tune; then \
	  echo ">>> Fine-tune container is RUNNING"; \
	  docker logs kengine-fine-tune --tail 20; \
	else \
	  echo ">>> Fine-tune container is NOT running. Start with 'make fine-tune-start'."; \
	fi

fine-tune-logs: ## Follow fine-tuning logs
	docker compose logs -f fine-tune

fine-tune-collect: ## Collect training data from knowledge base
	@echo ">>> Collecting training data..."
	docker compose exec -T scheduler php artisan geoflow:collect-training-data
	@echo ">>> Data collected. Check ./fine-tune/datasets/"

fine-tune-list-jobs: ## List completed fine-tuning jobs
	@ls -la ./fine-tune/output/ 2>/dev/null || echo "No output yet."

# =============================================================================
# Database
# =============================================================================
backup: ## Backup database
	@mkdir -p backups
	docker compose exec -T postgres pg_dump -U geo_user geo_flow > backups/kengine_$$(date +%Y%m%d_%H%M%S).sql

restore: ## Restore database (usage: make restore FILE=backup.sql)
	docker compose exec -T postgres psql -U geo_user -d geo_flow < $(FILE)

# =============================================================================
# Quality
# =============================================================================
privacy-check: ## Privacy scan
	$(PYTHON) ../scripts/privacy-check.py .

check: ## Verify required files
	@errors=0; for f in Makefile LICENSE README.md ARCHITECTURE.md .env.example docker-compose.yml scripts/setup.sh scripts/setup.ps1; do [ ! -f "$$f" ] && echo "Missing: $$f" && errors=$$((errors+1)); done; [ $$errors -eq 0 ] && echo "All files OK" || exit 1

test: check

# =============================================================================
# Maintenance
# =============================================================================
clean: ## Clean temp files
	rm -rf backups/ docker-data/

build: ## Build all Docker images
	docker compose build
	docker compose --profile all build
