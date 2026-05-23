"""Google Gemini provider — translates OpenAI request format to Gemini API."""

from __future__ import annotations

from typing import Any

import httpx

from .base import BaseProvider, ChatResponse, EmbeddingResponse


class GoogleProvider(BaseProvider):
    """Google Gemini provider via the Gemini API.

    Translates OpenAI-format chat requests to Gemini's generateContent format.
    """

    def _build_client(self) -> httpx.AsyncClient:
        base_url = self.config.base_url.rstrip("/")
        return httpx.AsyncClient(base_url=base_url, timeout=120.0)

    def _convert_messages(self, messages: list[dict]) -> tuple[list[dict], str | None]:
        """Convert OpenAI messages to Gemini format.

        Returns (gemini_contents, system_instruction).
        """
        system: str | None = None
        contents = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system = content if isinstance(content, str) else ""
                continue

            gemini_role = "model" if role == "assistant" else "user"

            if isinstance(content, str):
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}],
                })
            elif isinstance(content, list):
                parts = []
                for block in content:
                    if block.get("type") == "text":
                        parts.append({"text": block["text"]})
                    elif block.get("type") == "image_url":
                        img_url = block.get("image_url", {}).get("url", "")
                        parts.append({"text": f"[Image: {img_url}]"})
                contents.append({"role": gemini_role, "parts": parts})

        return contents, system

    async def chat(self, model: str, messages: list[dict], **kwargs) -> ChatResponse:
        client = self._build_client()
        try:
            contents, system = self._convert_messages(messages)

            payload: dict[str, Any] = {
                "contents": contents,
                "generationConfig": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "maxOutputTokens": kwargs.get("max_tokens", 4096),
                },
            }
            if system:
                payload["systemInstruction"] = {"parts": [{"text": system}]}

            api_key = self.config.api_key
            resp = await client.post(
                f"/v1beta/models/{model}:generateContent",
                params={"key": api_key},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            # Extract text from Gemini response
            content = ""
            candidates = data.get("candidates", [])
            if candidates:
                for part in candidates[0].get("content", {}).get("parts", []):
                    content += part.get("text", "")

            usage = data.get("usageMetadata", {})
            return ChatResponse(
                content=content,
                model=model,
                provider=self.name,
                finish_reason=candidates[0].get("finishReason", "STOP") if candidates else "STOP",
                usage={
                    "prompt_tokens": usage.get("promptTokenCount", 0),
                    "completion_tokens": usage.get("candidatesTokenCount", 0),
                },
            )
        finally:
            await client.aclose()

    async def embed(self, model: str, input_texts: list[str], **kwargs) -> EmbeddingResponse:
        client = self._build_client()
        try:
            api_key = self.config.api_key
            payload = {
                "model": f"models/{model}",
                "content": {"parts": [{"text": t}] for t in input_texts},
            }
            # Gemini embeddings: one request per text
            embeddings = []
            for text in input_texts:
                resp = await client.post(
                    f"/v1beta/models/{model}:embedContent",
                    params={"key": api_key},
                    json={"model": f"models/{model}", "content": {"parts": [{"text": text}]}},
                )
                resp.raise_for_status()
                data = resp.json()
                embeddings.append(data.get("embedding", {}).get("values", []))

            return EmbeddingResponse(
                embeddings=embeddings,
                model=model,
                provider=self.name,
            )
        finally:
            await client.aclose()

    async def list_models(self) -> list[str]:
        return [self.config.model]
