"""AI Gateway — Multi-provider AI routing proxy.

FastAPI server that provides an OpenAI-compatible API and routes requests
to the correct provider based on model name prefix.

Supports:
    - OpenAI, Anthropic Claude, Google Gemini, DeepSeek
    - Azure OpenAI, AWS Bedrock
    - Ollama, LM Studio, vLLM, LocalAI, llama.cpp
    - Any OpenAI-compatible custom endpoint
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from config import GatewayConfig
from router import AIRouter

logger = logging.getLogger("ai-gateway")

# Global state
config: GatewayConfig | None = None
router: AIRouter | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize gateway on startup."""
    global config, router
    config = GatewayConfig.from_env()
    router = AIRouter(config)

    if router.has_providers:
        logger.info("AI Gateway started with providers: %s", list(router.available_providers.keys()))
    else:
        logger.warning("No AI providers configured! Set at least one API key in .env")

    yield


app = FastAPI(
    title="GEOEngine AI Gateway",
    version="2.0.0",
    description="Multi-provider AI routing proxy for GEOEngine",
    lifespan=lifespan,
)


# =========================================================================
# OpenAI-compatible API endpoints
# =========================================================================

@app.get("/v1/models")
async def list_models():
    """List available models from all configured providers."""
    if not router or not router.has_providers:
        raise HTTPException(status_code=503, detail="No AI providers configured")

    models = []
    for provider_name, default_model in router.available_providers.items():
        provider = router._providers.get(provider_name)
        if provider:
            try:
                provider_models = await provider.list_models()
                for m in provider_models:
                    models.append({
                        "id": m,
                        "object": "model",
                        "created": 0,
                        "owned_by": provider_name,
                    })
            except Exception:
                models.append({
                    "id": default_model,
                    "object": "model",
                    "created": 0,
                    "owned_by": provider_name,
                })

    return {"object": "list", "data": models}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Chat completions endpoint — routes to correct provider."""
    if not router:
        raise HTTPException(status_code=503, detail="Gateway not initialized")

    body = await request.json()
    model = body.get("model", "")
    messages = body.get("messages", [])
    stream = body.get("stream", False)
    temperature = body.get("temperature", 0.7)
    max_tokens = body.get("max_tokens", 4096)

    if not model:
        raise HTTPException(status_code=400, detail="model is required")
    if not messages:
        raise HTTPException(status_code=400, detail="messages is required")

    provider = router.resolve(model)
    if not provider:
        available = ", ".join(router.available_providers.keys()) if router.has_providers else "none"
        raise HTTPException(
            status_code=400,
            detail=f"No configured provider for model '{model}'. Available providers: {available}",
        )

    logger.info("Routing model=%s -> provider=%s", model, provider.name)

    try:
        response = await provider.chat(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

        return JSONResponse({
            "id": "chatcmpl-ai-gateway",
            "object": "chat.completion",
            "created": 0,
            "model": response.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response.content},
                "finish_reason": response.finish_reason,
            }],
            "usage": response.usage,
            "provider": response.provider,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Provider %s error: %s", provider.name, str(e))
        raise HTTPException(status_code=502, detail=f"Provider {provider.name} error: {str(e)}")


@app.post("/v1/embeddings")
async def embeddings(request: Request):
    """Embeddings endpoint — routes to embedding provider."""
    if not router:
        raise HTTPException(status_code=503, detail="Gateway not initialized")

    body = await request.json()
    model = body.get("model", router._embedding_model)
    input_data = body.get("input", "")

    if isinstance(input_data, str):
        input_texts = [input_data]
    elif isinstance(input_data, list):
        input_texts = input_data
    else:
        raise HTTPException(status_code=400, detail="input must be a string or list of strings")

    provider = router.resolve_embedding(model)
    if not provider:
        raise HTTPException(status_code=400, detail=f"No embedding provider configured for model '{model}'")

    try:
        response = await provider.embed(model=model, input_texts=input_texts)

        data = []
        for i, emb in enumerate(response.embeddings):
            data.append({"object": "embedding", "index": i, "embedding": emb})

        return JSONResponse({
            "object": "list",
            "data": data,
            "model": response.model,
            "usage": response.usage,
            "provider": response.provider,
        })
    except Exception as e:
        logger.error("Embedding error: %s", str(e))
        raise HTTPException(status_code=502, detail=f"Embedding error: {str(e)}")


# =========================================================================
# Health check
# =========================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    provider_count = len(router.available_providers) if router else 0
    return {
        "status": "ok",
        "version": "2.0.0",
        "providers_configured": provider_count,
        "providers": list(router.available_providers.keys()) if router else [],
    }


# =========================================================================
# Entry point (for direct execution)
# =========================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AI_GATEWAY_PORT", "19090"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
