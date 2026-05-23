# KEngine Architecture v2.1

## Services

| Service | Port | Role |
|---------|------|------|
| **postgres** | 15432 | PostgreSQL 16 + pgvector for data and vector embeddings |
| **redis** | 16379 | Queue and cache backend |
| **app** | 18080 | Laravel 12 application serving Web UI + REST API |
| **queue** | - | Processes AI generation and knowledge processing tasks |
| **scheduler** | - | Triggers scheduled tasks every 60 seconds |
| **ai-gateway** | 19090 | Multi-provider AI routing proxy |
| **fine-tune** | - | Local model fine-tuning (on demand, GPU required) |

## Data Flow

```
Upload Documents → Auto Chunking → Vector Embedding → pgvector Store
    → RAG Retrieval → AI Generation (via Gateway) → Review → Publish → Archive
```

## AI Routing (v2.1)

```
Client (GEOFlow) → AI Gateway (:19090)
    ├── Model starts with "gpt-" / "o1" / "o3"       → OpenAI
    ├── Model starts with "claude"                     → Anthropic Claude
    ├── Model starts with "gemini"                     → Google Gemini
    ├── Model starts with "deepseek"                   → DeepSeek
    ├── Model starts with "glm-" / "GLM-"              → Zhipu AI
    ├── Model starts with "moonshot"                   → Moonshot
    ├── Model starts with "qwen" / "Qwen"              → Alibaba Qwen
    ├── Model starts with "ernie" / "ERNIE"            → Baidu Qianfan
    ├── Model starts with "ollama/"                    → Ollama (local)
    ├── Model starts with "lm-studio/"                 → LM Studio (local)
    ├── Model starts with "vllm/"                      → vLLM (local)
    └── Model starts with "localai/"                   → LocalAI (local)
```

## Knowledge Evolution (v2.1)

```
Scheduler (cron) → EvolutionJob → KnowledgeEvolutionService
    ├── 1. Score: Evaluate chunk quality via AI
    ├── 2. Merge: Detect and flag duplicates
    ├── 3. Summarize: Generate concise summaries
    ├── 4. Link: Discover cross-references
    └── 5. Prune: Archive stale low-quality chunks
```

## Fine-Tuning (v2.1)

```
Knowledge Chunks → CollectTrainingData Command → JSONL Dataset
    → Fine-Tune Container (Unsloth/PEFT)
    → LoRA Adapter → Deploy to Local Inference
```

## Security

- All service ports bound to 127.0.0.1
- Secrets via environment variables only
- No external network access for internal services
- API keys encrypted at rest (AES-256-CBC)
- AI Gateway does not log API keys
- Privacy scan in CI pipeline
