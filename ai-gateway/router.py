"""Model-based AI provider routing logic."""

from __future__ import annotations

from config import GatewayConfig
from providers import (
    AnthropicProvider,
    BaseProvider,
    GoogleProvider,
    OpenAICompatibleProvider,
)


class AIRouter:
    """Routes AI requests to the correct provider based on model name prefix."""

    def __init__(self, config: GatewayConfig):
        self.config = config
        self._providers: dict[str, BaseProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        """Initialize configured providers."""
        cfg = self.config

        # --- Cloud providers (OpenAI-compatible) ---
        if cfg.openai.enabled:
            self._providers["openai"] = OpenAICompatibleProvider("openai", cfg.openai)
        if cfg.deepseek.enabled:
            self._providers["deepseek"] = OpenAICompatibleProvider("deepseek", cfg.deepseek)
        if cfg.siliconflow.enabled:
            self._providers["siliconflow"] = OpenAICompatibleProvider("siliconflow", cfg.siliconflow)
        if cfg.zhipu.enabled:
            self._providers["zhipu"] = OpenAICompatibleProvider("zhipu", cfg.zhipu)
        if cfg.moonshot.enabled:
            self._providers["moonshot"] = OpenAICompatibleProvider("moonshot", cfg.moonshot)
        if cfg.qwen.enabled:
            self._providers["qwen"] = OpenAICompatibleProvider("qwen", cfg.qwen)

        # --- Cloud providers (non-OpenAI-compatible, need translation) ---
        if cfg.anthropic.enabled:
            self._providers["anthropic"] = AnthropicProvider("anthropic", cfg.anthropic)
        if cfg.gemini.enabled:
            self._providers["gemini"] = GoogleProvider("gemini", cfg.gemini)

        # --- Azure OpenAI (OpenAI-compatible but different endpoint) ---
        if cfg.azure.enabled:
            self._providers["azure"] = OpenAICompatibleProvider("azure", cfg.azure)

        # --- Local providers (all OpenAI-compatible) ---
        if cfg.ollama.enabled:
            self._providers["ollama"] = OpenAICompatibleProvider("ollama", cfg.ollama)
        if cfg.lm_studio.enabled:
            self._providers["lm_studio"] = OpenAICompatibleProvider("lm_studio", cfg.lm_studio)
        if cfg.vllm.enabled:
            self._providers["vllm"] = OpenAICompatibleProvider("vllm", cfg.vllm)
        if cfg.localai.enabled:
            self._providers["localai"] = OpenAICompatibleProvider("localai", cfg.localai)
        if cfg.llamacpp.enabled:
            self._providers["llamacpp"] = OpenAICompatibleProvider("llamacpp", cfg.llamacpp)
        if cfg.local_deepseek.enabled:
            self._providers["local_deepseek"] = OpenAICompatibleProvider("local_deepseek", cfg.local_deepseek)

        # --- Baidu (separate auth flow) ---
        if cfg.baidu.enabled:
            self._providers["baidu"] = OpenAICompatibleProvider("baidu", cfg.baidu)

        # Embedding
        self._embedding_model = cfg.embedding_model
        self._embedding_provider_name = cfg.embedding_provider

    # Model prefix -> provider mapping
    MODEL_ROUTES: dict[str, str] = {
        # OpenAI
        "gpt-": "openai",
        "o1": "openai",
        "o3": "openai",
        "text-embedding": "openai",
        "tts-": "openai",
        "dall-e": "openai",
        # Anthropic Claude
        "claude": "anthropic",
        # Google Gemini
        "gemini": "gemini",
        # DeepSeek
        "deepseek": "deepseek",
        # Azure OpenAI
        "azure-": "azure",
        # SiliconFlow
        "siliconflow": "siliconflow",
        "Pro/": "siliconflow",
        "deepseek-ai/": "siliconflow",
        "Qwen/": "siliconflow",
        "THUDM/": "siliconflow",
        "BAAI/": "siliconflow",
        "internlm/": "siliconflow",
        # Zhipu
        "glm-": "zhipu",
        "GLM-": "zhipu",
        "charglm-": "zhipu",
        "cogview-": "zhipu",
        # Moonshot / Kimi
        "moonshot": "moonshot",
        # Baidu
        "ernie": "baidu",
        "ERNIE": "baidu",
        # Alibaba Qwen
        "qwen": "qwen",
        "Qwen": "qwen",
        # Ollama (local)
        "ollama/": "ollama",
        # LM Studio (local)
        "lm-studio/": "lm_studio",
        # vLLM (local)
        "vllm/": "vllm",
        # LocalAI
        "localai/": "localai",
        # llama.cpp
        "llamacpp/": "llamacpp",
        # Local DeepSeek
        "local-deepseek": "local_deepseek",
    }

    def resolve(self, model: str) -> BaseProvider | None:
        """Resolve a model name to a provider instance."""
        for prefix, provider_name in self.MODEL_ROUTES.items():
            if model.startswith(prefix):
                provider = self._providers.get(provider_name)
                if provider and provider.enabled:
                    return provider
        return None

    def resolve_embedding(self, model: str | None = None) -> BaseProvider | None:
        """Resolve an embedding model to a provider."""
        model = model or self._embedding_model
        provider_name = self._embedding_provider_name
        provider = self._providers.get(provider_name)
        if provider and provider.enabled:
            return provider
        # Fallback: try to find any enabled provider
        for p in self._providers.values():
            if p.enabled:
                return p
        return None

    @property
    def available_providers(self) -> dict[str, str]:
        """Return mapping of provider name -> default model."""
        result: dict[str, str] = {}
        for name, provider in self._providers.items():
            if provider.enabled:
                result[name] = provider.config.model
        return result

    @property
    def has_providers(self) -> bool:
        """Check if any provider is configured."""
        return any(p.enabled for p in self._providers.values())
