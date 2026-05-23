<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge" alt="">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker" alt="">
  <img src="https://img.shields.io/badge/PHP_8.2+-777BB4?style=for-the-badge&logo=php" alt="">
  <img src="https://img.shields.io/badge/PostgreSQL_pgvector-336791?style=for-the-badge&logo=postgresql" alt="">
</p>

<p align="center"><b>English</b> · <a href="README_CN.md">中文</a></p>
<p align="center"><b>GEO Content Engineering Infrastructure</b></p>
<p align="center"><i>Knowledge → Generate → Distribute → Analyze — Transform trusted knowledge into publishable, distributable, trackable GEO content assets.</i></p>

---

## Overview

GEOEngine is a production-ready deployment kit for GEOFlow, the leading open-source GEO content engineering platform. It orchestrates the entire content lifecycle — from knowledge ingestion and AI generation through review, multi-site distribution, and performance analytics — into one cohesive system that runs 100% on your infrastructure.

### System Architecture

```mermaid
flowchart TB
    subgraph User["Users"]
        A[Admin] -->|manage| B[Web UI]
        C[API Client] -->|consume| D[REST API]
    end
    subgraph Core["GEOEngine Core"]
        B --> E[Laravel 12]
        D --> E
        E --> F[(PostgreSQL+pgvector)]
        E --> G[(Redis)]
    end
    subgraph Workers["Workers"]
        H[Scheduler] -->|scan| I[Queue Worker]
        I -->|AI gen| J[AI API]
        I -->|RAG| K[(Vector Store)]
    end
    subgraph Output["Output"]
        L[Review/Publish] --> M[Articles]
        M --> N[Distribution]
        N --> O[Target Sites]
    end
    E --> L; J --> M; K --> I
```

### Pipeline Overview

```mermaid
flowchart LR
    subgraph In["Input"]
        KB[Knowledge Base] --> VC[Vectorize]
        TL[Titles] --> TP[Pool]
        KL[Keywords] --> KP[Pool]
    end
    subgraph P["Process"]
        TP --> TASK[Task Engine]
        KP --> TASK; RAG[RAG] --> TASK
        TASK --> AI[AI Generation]
    end
    subgraph Rev["Review"]
        AI --> DRAFT[Draft] --> RV[Review Gate]
        RV -->|Approve| PUB[Published]
        RV -->|Reject| REJ[Rejected]
    end
    subgraph Out["Distribute"]
        PUB --> LOCAL[Local Site]
        PUB --> DIST[Queue] --> SITES[Target Sites]
    end
    VC --> RAG
    SITES --> STATS[Analytics]
    LOCAL --> STATS
```

### Task Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created: Admin creates
    Created --> Scheduled: Scheduler picks
    Scheduled --> Generating: Worker starts
    Generating --> DraftReady: AI returns
    Generating --> Failed: API error
    Failed --> Scheduled: Retry
    DraftReady --> InReview: Admin reviews
    InReview --> Published: Approved
    InReview --> Rejected: Declined
    Published --> Distributed: To targets
    Published --> Archived
    Rejected --> [*]
    Archived --> [*]
```

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/justmicos/geo-engine.git
cd geo-engine
make dev-setup
# Edit .env -> set AI_API_KEY (required)
make dev-up

# Verify
make dev-status
open http://localhost:18080/geo_admin
```

## Features

| Area | Capabilities |
|------|-------------|
| Knowledge Engine | Upload docs, auto-chunk, pgvector, RAG retrieval |
| Content Factory | Title/keyword/image libraries, AI generation, review pipeline |
| Distribution | Channel management, Agent protocol, WordPress integration |
| Analytics | System overview, per-site ops, distribution tracking, AI crawler detection |

## Commands

```bash
make dev-setup     # One-click setup
make dev-up        # Start services
make dev-down      # Stop services
make dev-logs      # Follow logs
make backup        # Backup database
make restore FILE=x  # Restore from backup
make privacy-check # Privacy leak scan
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| AI_API_KEY | YES | - | AI provider API key |
| AI_API_URL | No | https://api.deepseek.com/v1 | API endpoint |
| AI_MODEL | No | deepseek-chat | Model name |
| APP_PORT | No | 18080 | Web UI port |
| SITE_NAME | No | GEOEngine | Site name |

## License

MIT License -- see [LICENSE](LICENSE).

Built on [GEOFlow](https://github.com/yaojingang/GEOFlow) by yaojingang (Apache 2.0).
