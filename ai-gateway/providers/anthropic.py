"""Anthropic Claude provider — translates OpenAI request format to Anthropic Messages API."""

from __future__ import annotations

from typing import Any

import httpx

from .base import BaseProvider, ChatResponse, EmbeddingResponse


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider via Messages API.

    Translates OpenAI-format chat requests to Anthropic's Messages format.
    Embeddings are not supported by Anthropic directly; falls back to config.
    """

    _ANTHROPIC_VERSION = "2023-06-01"

    def _build_client(self) -> httpx.AsyncClient:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": self.config.api_key or getattr(self.config, "api_version", None) or self._ANTHROPIC_VERSION,
        }
        base_url = self.config.base_url.rstrip("/")
        return httpx.AsyncClient(base_url=base_url, headers=headers, timeout=120.0)

    def _convert_messages(self, messages: list[dict]) -> tuple[list[dict], str | None]:
        """Convert OpenAI messages to Anthropic format.

        Returns (anthropic_messages, system_prompt).
        """
        system: str | None = None
        anthropic_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system = content if isinstance(content, str) else content[0].get("text", "") if isinstance(content, list) else ""
                continue

            anthropic_role = "assistant" if role == "assistant" else "user"

            if isinstance(content, str):
                anthropic_messages.append({"role": anthropic_role, "content": content})
            elif isinstance(content, list):
                blocks = []
                for block in content:
                    if block.get("type") == "image_url":
                        # Convert image_url to Anthropic image format
                        img_data = block.get("image_url", {}).get("url", "")
                        if img_data.startswith("data:"):
                            media_type, base64_data = img_data.split(",", 1)
                            media_type = media_type.replace("data:", "").replace(";base64", "")
                            blocks.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_data,
                                },
                            })
                        else:
                            blocks.append({"type": "text", "text": f"[Image: {img_data}]"})
                    elif block.get("type") == "text":
                        blocks.append({"type": "text", "text": block["text"]})
                anthropic_messages.append({"role": anthropic_role, "content": blocks})

        return anthropic_messages, system

    async def chat(self, model: str, messages: list[dict], **kwargs) -> ChatResponse:
        client = self._build_client()
        try:
            anthropic_messages, system = self._convert_messages(messages)

            payload: dict[str, Any] = {
                "model": model,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "temperature": kwargs.get("temperature", 0.7),
            }
            if system:
                payload["system"] = system

            resp = await client.post("/v1/messages", json=payload)
            resp.raise_for_status()
            data = resp.json()

            # Extract text content from Anthropic response
            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")

            usage = data.get("usage", {})
            return ChatResponse(
                content=content,
                model=data.get("model", model),
                provider=self.name,
                finish_reason=data.get("stop_reason", "end_turn"),
                usage={
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                },
            )
        finally:
            await client.aclose()

    async def embed(self, model: str, input_texts: list[str], **kwargs) -> EmbeddingResponse:
        """Anthropic does not offer embeddings. Return empty."""
        return EmbeddingResponse(
            embeddings=[[0.0] * 3072 for _ in input_texts],
            model=model,
            provider=self.name,
        )

    async def list_models(self) -> list[str]:
        return [self.config.model]
