# GEOEngine — GEO Content Engineering Infrastructure

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docs.docker.com/compose/)

Knowledge → Generate → Distribute → Track — open-source GEO content engineering.

## Quick Start
```bash
git clone https://github.com/SATPROTOCOL/micos.git
cd micos/geo-engine
make dev-setup
# Edit .env → set AI_API_KEY
make dev-up
```

## Features
- Knowledge Base with RAG (pgvector)
- AI Content Generation (OpenAI-compatible)
- Multi-site Distribution via Agent protocol
- Analytics Dashboard
- All local, no data leaves your network

## Documentation
- [Architecture](ARCHITECTURE.md)
- [Configuration](.env.example)
- [Contributing](CONTRIBUTING.md)

## License
MIT — see [LICENSE](LICENSE).

## Acknowledgments
Built on [GEOFlow](https://github.com/yaojingang/GEOFlow) by yaojingang (Apache 2.0).
