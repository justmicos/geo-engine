"""Dataset handling for fine-tuning — loads JSONL files in Alpaca/ShareGPT format."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("fine-tune.dataset")


def load_dataset(path: str | Path, max_samples: int = 0, format: str = "alpaca") -> list[dict]:
    """Load a JSONL dataset file.

    Args:
        path: Path to JSONL file
        max_samples: Max samples (0 = all)
        format: 'alpaca' (instruction/input/output) or 'sharegpt' (conversations)

    Returns:
        List of formatted samples
    """
    path = Path(path)
    if not path.exists():
        logger.warning("Dataset not found: %s", path)
        return []

    samples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                sample = json.loads(line)
                formatted = _format_sample(sample, format)
                if formatted:
                    samples.append(formatted)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON line, skipping")

            if max_samples > 0 and len(samples) >= max_samples:
                break

    logger.info("Loaded %d samples from %s", len(samples), path)
    return samples


def _format_sample(sample: dict, format: str) -> dict | None:
    """Format a single sample."""
    if format == "sharegpt":
        conversations = sample.get("conversations", [])
        if not conversations or not isinstance(conversations, list):
            return None
        return {"conversations": conversations}

    # Default: Alpaca format
    instruction = sample.get("instruction", "")
    input_text = sample.get("input", "")
    output = sample.get("output", "")

    if not output:
        return None

    if input_text:
        text = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
    else:
        text = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"

    return {"text": text}


def list_datasets(datasets_dir: str | Path = "/app/datasets") -> list[dict]:
    """List available datasets in the datasets directory."""
    datasets_dir = Path(datasets_dir)
    if not datasets_dir.exists():
        return []

    results = []
    for f in sorted(datasets_dir.glob("*.jsonl")):
        size = f.stat().st_size
        results.append({
            "name": f.name,
            "path": str(f),
            "size_bytes": size,
            "size_mb": round(size / 1024 / 1024, 2),
        })

    return results
