# Changelog

## [2.1.0] — 2026-05-23

### Added
- **Multi-Provider AI Gateway** (`ai-gateway/`): OpenAI-compatible proxy routing to 15+ providers (OpenAI, Anthropic, Google, DeepSeek, Azure, AWS Bedrock, SiliconFlow, Zhipu, Moonshot, Qwen, Baidu, Ollama, LM Studio, vLLM, LocalAI, llama.cpp)
- **Knowledge Auto-Evolution** (`KnowledgeEvolutionService`): Periodic quality scoring, deduplication, summarization, cross-referencing, and stale content archiving
- **Local Model Fine-Tuning** (`fine-tune/`): Docker-based LoRA/QLoRA fine-tuning with Unsloth and PEFT; collects training data from knowledge base content
- **GEOFlow Patches** (`patches/`): Extended `OpenAiRuntimeProvider::resolveChatDriver()` with local LLM + Anthropic + Gemini + Azure detection; new config entries for AI Gateway, evolution, and fine-tuning
- **Configuration**: Complete `.env.example` with all provider configs; auto-detect Ollama/LM Studio in setup scripts

### Changed
- `docker-compose.yml`: Added `ai-gateway` and `fine-tune` services with profile-based activation
- `Makefile`: Added 15+ new commands for gateway, evolution, and fine-tuning management
- `setup.sh` / `setup.ps1`: Auto-detect local LLM engines; apply patches after clone
- `README.md` / `README_CN.md`: Full documentation for all new features
- `ARCHITECTURE.md`: Updated architecture diagram with AI Gateway and evolution flow

### Security
- Enhanced CI privacy scanning with regex-based secret detection
- AI Gateway uses `.env`-managed API keys (never hardcoded)
- Fine-tuning datasets isolated in `fine-tune/datasets/` (gitignored)

## [1.0.0] — 2026-05-23

- Initial release of KEngine knowledge base platform
- Document management with automatic chunking and vectorization
- AI-powered semantic search and Q&A via RAG
- Cross-platform Docker deployment (Linux/macOS/Windows)
- GitHub Actions CI with privacy scanning
- MIT License
