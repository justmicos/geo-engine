# GEOEngine Architecture

## Services
- **postgres**: PostgreSQL 16 + pgvector for data and embeddings
- **redis**: Queue and cache backend
- **geoflow**: Laravel 12 — Web UI + REST API
- **queue**: Processes AI generation and distribution tasks
- **scheduler**: Triggers scheduled tasks every 60 seconds

## Data Flow
```
User → Task → AI Generation (with RAG) → Draft → Review → Publish → Distribute → Analytics
```

## Security
- All service ports bound to 127.0.0.1
- Secrets via environment variables only
- No external network access for internal services
