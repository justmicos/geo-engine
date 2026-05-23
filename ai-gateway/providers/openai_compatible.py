"""OpenAI-compatible provider — covers OpenAI, DeepSeek, Ollama, LM Studio, vLLM, and any OpenAI-compatible API."""

from __future__ import annotations

from typing import Any

import httpx

from .base import BaseProvider, ChatResponse, EmbeddingResponse


class OpenAICompatibleProvider(BaseProvider):
    """Provider for any OpenAI-compatible chat/embedding API.

    Works with: OpenAI, DeepSeek, SiliconFlow, Zhipu, Moonshot, Qwen,
    Ollama, LM Studio, vLLM, LocalAI, llama.cpp, and any OpenAI-compatible endpoint.
    """

    def _build_client(self) -> httpx.AsyncClient:
        headers = {"Content-Type": "application/json"}
        api_key = self.config.api_key or ""
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if self.config.org_id:
            headers["OpenAI-Organization"] = self.config.org_id

        base_url = self.config.base_url.rstrip("/")
        return httpx.AsyncClient(base_url=base_url, headers=headers, timeout=120.0)

    async def chat(self, model: str, messages: list[dict], **kwargs) -> ChatResponse:
        client = self._build_client()
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096),
            }
            if "stream" in kwargs:
                payload["stream"] = kwargs["stream"]

            resp = await client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()

            choice = data["choices"][0]
            content = choice.get("message", {}).get("content", "")
            if content is None:
                content = ""

            return ChatResponse(
                content=content,
                model=data.get("model", model),
                provider=self.name,
                finish_reason=choice.get("finish_reason", "stop"),
                usage=data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0}),
            )
        finally:
            await client.aclose()

    async def embed(self, model: str, input_texts: list[str], **kwargs) -> EmbeddingResponse:
        client = self._build_client()
        try:
            payload = {
                "model": model,
                "input": input_texts if len(input_texts) > 1 else input_texts[0],
            }
            resp = await client.post("/embeddings", json=payload)
            resp.raise_for_status()
            data = resp.json()

            # Normalize response to always return list of embeddings
            raw_data = data["data"]
            if isinstance(raw_data, dict):
                raw_data = [raw_data]

            embeddings = [item["embedding"] for item in raw_data]

            return EmbeddingResponse(
                embeddings=embeddings,
                model=data.get("model", model),
                provider=self.name,
                usage=data.get("usage", {"prompt_tokens": 0}),
            )
        finally:
            await client.aclose()

    async def list_models(self) -> list[str]:
        client = self._build_client()
        try:
            resp = await client.get("/models")
            resp.raise_for_status()
            data = resp.json()
            return [m["id"] for m in data.get("data", [])]
        except Exception:
            return [self.config.model]
        finally:
            await client.aclose()
