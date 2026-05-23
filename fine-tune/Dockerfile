# Fine-tuning container — supports Unsloth (preferred) and vanilla PEFT/QLoRA
# Requires: NVIDIA GPU with CUDA 12.1+

# Stage 1: Use Unsloth for optimized training if available
FROM unslothai/unsloth:latest AS unsloth-base

WORKDIR /app

# Stage 2: Fallback — vanilla PyTorch + PEFT for broader compatibility
FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime AS torch-base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final: try Unsloth first, fall back to vanilla
FROM unsloth-base AS final

# If Unsloth build fails, the torch-base stage is used instead
# Default to torch-base since Unsloth may not be available in all environments
FROM torch-base

COPY . /app/
RUN mkdir -p /app/output /app/datasets

ENTRYPOINT ["python", "/app/fine_tune.py"]
CMD ["--help"]
