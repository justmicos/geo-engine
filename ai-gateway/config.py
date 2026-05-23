"""AI Gateway configuration — loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProviderConfig:
    """Base configuration for an AI provider."""

    enabled: bool = False
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    org_id: str = ""


@dataclass
class GatewayConfig:
    """Aggregate configuration from environment variables."""

    # Gateway settings
    port: int = 19090
    log_level: str = "info"
    workers: int = 1

    # Cloud providers
    openai: ProviderConfig = field(default_factory=ProviderConfig)
    anthropic: ProviderConfig = field(default_factory=ProviderConfig)
    gemini: ProviderConfig = field(default_factory=ProviderConfig)
    deepseek: ProviderConfig = field(default_factory=ProviderConfig)
    azure: ProviderConfig = field(default_factory=ProviderConfig)
    aws_bedrock: ProviderConfig = field(default_factory=ProviderConfig)
    siliconflow: ProviderConfig = field(default_factory=ProviderConfig)
    zhipu: ProviderConfig = field(default_factory=ProviderConfig)
    moonshot: ProviderConfig = field(default_factory=ProviderConfig)
    baidu: ProviderConfig = field(default_factory=ProviderConfig)
    qwen: ProviderConfig = field(default_factory=ProviderConfig)

    # Local providers
    ollama: ProviderConfig = field(default_factory=ProviderConfig)
    lm_studio: ProviderConfig = field(default_factory=ProviderConfig)
    vllm: ProviderConfig = field(default_factory=ProviderConfig)
    localai: ProviderConfig = field(default_factory=ProviderConfig)
    llamacpp: ProviderConfig = field(default_factory=ProviderConfig)
    local_deepseek: ProviderConfig = field(default_factory=ProviderConfig)

    # Embedding
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    @classmethod
    def from_env(cls) -> GatewayConfig:
        cfg = cls()

        cfg.port = int(os.getenv("AI_GATEWAY_PORT", "19090"))
        cfg.log_level = os.getenv("AI_GATEWAY_LOG_LEVEL", "info")
        cfg.workers = int(os.getenv("AI_GATEWAY_WORKERS", "1"))

        # OpenAI
        cfg.openai = ProviderConfig(
            enabled=bool(os.getenv("OPENAI_API_KEY")),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url="https://api.openai.com/v1",
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            org_id=os.getenv("OPENAI_ORG_ID", ""),
        )

        # Anthropic Claude
        cfg.anthropic = ProviderConfig(
            enabled=bool(os.getenv("ANTHROPIC_API_KEY")),
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            base_url="https://api.anthropic.com",
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        )

        # Google Gemini
        cfg.gemini = ProviderConfig(
            enabled=bool(os.getenv("GEMINI_API_KEY")),
            api_key=os.getenv("GEMINI_API_KEY", ""),
            base_url="https://generativelanguage.googleapis.com",
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-pro"),
        )

        # DeepSeek
        cfg.deepseek = ProviderConfig(
            enabled=bool(os.getenv("DEEPSEEK_API_KEY")),
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        )

        # Azure OpenAI
        cfg.azure = ProviderConfig(
            enabled=bool(os.getenv("AZURE_OPENAI_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT")),
            api_key=os.getenv("AZURE_OPENAI_KEY", ""),
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            model=os.getenv("AZURE_OPENAI_MODEL", "gpt-4o"),
        )

        # AWS Bedrock
        cfg.aws_bedrock = ProviderConfig(
            enabled=bool(os.getenv("AWS_ACCESS_KEY_ID")),
            api_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            base_url=os.getenv("AWS_REGION", "us-east-1"),
            model=os.getenv("AWS_BEDROCK_MODEL", "claude-sonnet-4-v2"),
        )

        # SiliconFlow
        cfg.siliconflow = ProviderConfig(
            enabled=bool(os.getenv("SILICONFLOW_API_KEY")),
            api_key=os.getenv("SILICONFLOW_API_KEY", ""),
            base_url=os.getenv("SILICONFLOW_API_URL", "https://api.siliconflow.cn/v1"),
            model=os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3"),
        )

        # Zhipu AI
        cfg.zhipu = ProviderConfig(
            enabled=bool(os.getenv("ZHIPU_API_KEY")),
            api_key=os.getenv("ZHIPU_API_KEY", ""),
            base_url="https://open.bigmodel.cn/api/paas/v4",
            model=os.getenv("ZHIPU_MODEL", "glm-4-plus"),
        )

        # Moonshot
        cfg.moonshot = ProviderConfig(
            enabled=bool(os.getenv("MOONSHOT_API_KEY")),
            api_key=os.getenv("MOONSHOT_API_KEY", ""),
            base_url="https://api.moonshot.cn/v1",
            model=os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k"),
        )

        # Baidu Qianfan (handles auth differently)
        cfg.baidu = ProviderConfig(
            enabled=bool(os.getenv("BAIDU_API_KEY") and os.getenv("BAIDU_SECRET_KEY")),
            api_key=os.getenv("BAIDU_API_KEY", ""),
            base_url=os.getenv("BAIDU_SECRET_KEY", ""),
            model=os.getenv("BAIDU_MODEL", "ernie-4.0"),
        )

        # Alibaba Qwen
        cfg.qwen = ProviderConfig(
            enabled=bool(os.getenv("QWEN_API_KEY")),
            api_key=os.getenv("QWEN_API_KEY", ""),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=os.getenv("QWEN_MODEL", "qwen-max"),
        )

        # Ollama (local)
        cfg.ollama = ProviderConfig(
            enabled=bool(os.getenv("OLLAMA_BASE_URL")),
            api_key="",  # local, no key needed
            base_url=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:72b"),
        )

        # LM Studio (local)
        cfg.lm_studio = ProviderConfig(
            enabled=bool(os.getenv("LMSTUDIO_BASE_URL")),
            api_key="",  # local, no key needed
            base_url=os.getenv("LMSTUDIO_BASE_URL", "http://host.docker.internal:1234"),
            model=os.getenv("LMSTUDIO_MODEL", "qwen2.5-72b-gguf"),
        )

        # vLLM (local)
        cfg.vllm = ProviderConfig(
            enabled=bool(os.getenv("VLLM_BASE_URL")),
            api_key="",  # local
            base_url=os.getenv("VLLM_BASE_URL", "http://host.docker.internal:8000"),
            model=os.getenv("VLLM_MODEL", "qwen2.5-72b-instruct"),
        )

        # LocalAI
        cfg.localai = ProviderConfig(
            enabled=bool(os.getenv("LOCALAI_BASE_URL")),
            api_key="",
            base_url=os.getenv("LOCALAI_BASE_URL", "http://host.docker.internal:8080"),
            model=os.getenv("LOCALAI_MODEL", "llama-3.1-8b-instruct"),
        )

        # llama.cpp
        cfg.llamacpp = ProviderConfig(
            enabled=bool(os.getenv("LLAMACPP_BASE_URL")),
            api_key="",
            base_url=os.getenv("LLAMACPP_BASE_URL", "http://host.docker.internal:8081"),
            model=os.getenv("LLAMACPP_MODEL", "qwen2.5-72b-q4km"),
        )

        # Local DeepSeek
        cfg.local_deepseek = ProviderConfig(
            enabled=bool(os.getenv("LOCAL_DEEPSEEK_BASE_URL")),
            api_key="",
            base_url=os.getenv("LOCAL_DEEPSEEK_BASE_URL", "http://host.docker.internal:8000"),
            model=os.getenv("LOCAL_DEEPSEEK_MODEL", "deepseek-ai/DeepSeek-V3"),
        )

        # Embedding
        cfg.embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai")
        cfg.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        return cfg
