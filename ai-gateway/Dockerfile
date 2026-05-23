FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE ${AI_GATEWAY_PORT:-19090}

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${AI_GATEWAY_PORT:-19090} --workers ${AI_GATEWAY_WORKERS:-1} --log-level ${AI_GATEWAY_LOG_LEVEL:-info}"]
