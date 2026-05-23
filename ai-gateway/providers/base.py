"""Base provider interface for AI Gateway."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatResponse:
    """Standardized chat completion response."""

    content: str
    model: str
    provider: str
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0})


@dataclass
class EmbeddingResponse:
    """Standardized embedding response."""

    embeddings: list[list[float]]
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 0})


class BaseProvider(ABC):
    """Abstract base class for all AI providers."""

    def __init__(self, name: str, config: Any):
        self.name = name
        self.config = config

    @property
    def enabled(self) -> bool:
        return self.config.enabled if hasattr(self.config, "enabled") else False

    @abstractmethod
    async def chat(self, model: str, messages: list[dict], **kwargs) -> ChatResponse:
        """Send a chat completion request."""
        ...

    @abstractmethod
    async def embed(self, model: str, input_texts: list[str], **kwargs) -> EmbeddingResponse:
        """Send an embedding request."""
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models from this provider."""
        ...
