<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-success" alt="Status">
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/PHP-8.2%2B-777BB4?logo=php" alt="PHP">
  <img src="https://img.shields.io/badge/PostgreSQL-pgvector-336791?logo=postgresql" alt="PostgreSQL">
</p>

# GEOEngine

> **Knowledge → Generate → Distribute → Analyze** — Open-source GEO content engineering infrastructure that transforms trusted knowledge into publishable, distributable, trackable content assets.

---

## Overview

GEOEngine is a production-ready deployment kit for [GEOFlow](https://github.com/yaojingang/GEOFlow), the leading open-source GEO (Generative Engine Optimization) content engineering platform. It orchestrates the entire content lifecycle — from knowledge ingestion and AI generation through review, multi-site distribution, and performance analytics — into one cohesive system that runs entirely on your infrastructure.

### What makes GEOEngine different

| Aspect | GEOEngine |
|--------|-----------|
| **Knowledge First** | Upload source materials, auto-chunk, vectorize with pgvector, retrieve via RAG |
| **AI-Native** | OpenAI-compatible API for both chat and embeddings with automatic failover |
| **Multi-Site by Design** | Distribute content across unlimited target sites via Agent protocol |
| **Analytics Built-In** | Track views, AI crawler activity, and distribution status out of the box |
| **Privacy First** | 100% local deployment. No data, no API keys, no content leaves your network |
| **Zero Lock-in** | Standard Docker Compose, PostgreSQL, Redis — no proprietary infrastructure |

---

## ✨ Features

### Knowledge Engine
- Upload documents (Markdown, plain text) for automatic chunking and vectorization
- pgvector-powered semantic search via RAG (Retrieval-Augmented Generation)
- Embedding model auto-configuration with OpenAI-compatible APIs

### Content Factory
- **Material Management**: Title libraries, keyword libraries, image libraries, authors
- **AI Generation**: Schedule content production with configurable models, prompts, and cadence
- **Review Pipeline**: Draft → Review → Publish → Recycle with batch operations
- **SEO Ready**: Schema.org structured data, Open Graph, sitemaps, `llms.txt`

### Distribution Network
- **Channel Management**: Create unlimited distribution channels with per-channel secrets
- **Target Site Packages**: Download pre-configured PHP Agent packages for each target
- **Remote Sync**: Push articles, sync settings, manage remote content from one dashboard
- **WordPress Integration**: Native WordPress REST API publisher included

### Analytics Dashboard
- System overview with content production metrics
- Per-site content operations analytics
- Multi-site distribution tracking
- Access logs with AI crawler identification
- Top content and top channel performance

---

## 🚀 Quick Start

### Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Docker | 24+ |
| Docker Compose | 2.20+ |
| Git | 2.30+ |

### One-Click Setup (Linux / macOS)

```bash
git clone https://github.com/justmicos/geo-engine.git
cd geo-engine
make dev-setup
# Edit .env → set AI_API_KEY (required)
make dev-up
```

### Windows Setup

```powershell
git clone https://github.com/justmicos/geo-engine.git
cd geo-engine
.\scripts\setup.ps1
# Edit .env → set AI_API_KEY
docker compose up -d
```

### Verify

```bash
# Check all services are running
make dev-status

# Open the admin dashboard
open http://localhost:18080/geo_admin

# Run health check
bash scripts/health-check.sh
```

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Web / Admin                           │
│               Laravel 12 (Blade + REST API)                   │
├──────────────────────────────────────────────────────────────┤
│   Scheduler     │     Queue      │     Worker                 │
│   (cron-like)   │  (Redis-based) │  (AI generation tasks)    │
├─────────┬────────┬────────┬──────┴──────┬─────────────────────┤
│ Know-   │  AI    │Review  │  Distribute │  Analytics          │
│ ledge   │  Gen   │&Pub-   │  Multi-site │  Views / Crawlers   │
│ Base+   │  en-   │lish    │  Agent      │  / Distribution     │
│ RAG     │  rate  │        │  Protocol   │                     │
├─────────┴────────┴────────┴─────────────┴─────────────────────┤
│  PostgreSQL (pgvector)    │    Redis (Cache / Queue)          │
└──────────────────────────────────────────────────────────────┘
```

### Services

| Container | Role | Port (host) |
|-----------|------|-------------|
| `geoengine-postgres` | PostgreSQL 16 + pgvector | `127.0.0.1:15432` |
| `geoengine-redis` | Cache & queue backend | `127.0.0.1:16379` |
| `geoengine-app` | Laravel application (Web UI + API) | `127.0.0.1:18080` |
| `geoengine-queue` | Queue worker (AI generation) | — |
| `geoengine-scheduler` | Task scheduler (every 60s) | — |

---

## 📋 Commands Reference

```bash
make dev-setup        # Clone GEOFlow + configure .env
make dev-up           # Start all services
make dev-down         # Stop all services
make dev-logs         # Follow all service logs
make dev-status       # Show service status

make backup           # Backup PostgreSQL database
make restore FILE=x   # Restore from backup

make privacy-check    # Scan for privacy leaks (publish gate)
make check            # Verify all required files exist
```

---

## ⚙️ Configuration

All settings are managed through `.env`. Copy `.env.example` and customize:

```bash
cp .env.example .env
```

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `AI_API_KEY` | Your AI provider API key | `sk-xxxxxxxxxxxxxxxx` |

### Optional Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_API_URL` | `https://api.deepseek.com/v1` | AI API endpoint |
| `AI_MODEL` | `deepseek-chat` | Model for content generation |
| `SITE_NAME` | `GEOEngine` | Your site name |
| `APP_PORT` | `18080` | Web UI port |
| `POSTGRES_PASSWORD` | auto-generated | Database password |
| `APP_LOCALE` | `en` | Admin interface language |

---

## 📂 Project Structure

```
geo-engine/
├── docker-compose.yml         # Service orchestration (5 containers)
├── .env.example               # Configuration template with docs
├── Makefile                   # 10 management commands
├── scripts/
│   ├── setup.sh               # Linux/macOS installer
│   ├── setup.ps1              # Windows installer
│   ├── health-check.sh        # Service verification
│   ├── backup.sh              # Database backup
│   └── seed-kb.sh             # Knowledge base importer
├── config/
│   ├── nginx/default.conf     # Production Nginx config
│   └── target-site/server.py  # Target site reference server
├── seed/
│   └── knowledge-base.md      # Sample knowledge base content
├── .github/workflows/ci.yml   # CI: privacy + file integrity
├── ARCHITECTURE.md            # Detailed architecture docs
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # Contribution guide
└── LICENSE                    # MIT License
```

---

## 🔒 Security

- **All ports bind to 127.0.0.1** — no external access by default
- **No secrets in code** — all credentials via `.env` environment variables
- **Privacy gate** — `make privacy-check` must pass before any release
- **Dependency scanning** — GitHub Dependabot integration ready

---

## 📖 Use Case Examples

### Content Marketing Team
```
Knowledge Base (product specs, case studies, whitepapers)
  → AI generates GEO-optimized articles
  → Review and approve in dashboard
  → Distribute to 3 regional sites
  → Track crawler engagement per site
```

### Personal Knowledge Publisher
```
LLM Wiki / Obsidian notes → Export to knowledge base
  → AI generates explanatory articles
  → Publish to personal blog + Dev.to
  → Monitor GEO visibility
```

### Enterprise Content Operations
```
Centralized content team manages 1 knowledge base
  → 10 automated content streams
  → 5 target sites across regions
  → Analytics-driven content strategy
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE).

## 🙏 Acknowledgments

Built on [GEOFlow](https://github.com/yaojingang/GEOFlow) by yaojingang (Apache 2.0).

---

<p align="center">
  <sub>Built with ❤️ for the open-source GEO community</sub>
</p>
