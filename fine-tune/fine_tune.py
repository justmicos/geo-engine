#!/usr/bin/env python3
"""
GEOEngine Fine-Tuning Pipeline — LoRA/QLoRA fine-tuning for local LLMs.

Supports:
  - Alpaca and ShareGPT format datasets
  - LoRA, QLoRA, and full fine-tuning
  - Configurable via environment variables or CLI args
  - Output to /app/fine-tune/output/

Usage:
  python fine_tune.py --dataset /app/datasets/training.jsonl --base-model Qwen/Qwen2.5-7B-Instruct
  python fine_tune.py --list-datasets
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import torch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fine-tune")


def get_env_config() -> dict[str, Any]:
    """Read configuration from environment variables."""
    return {
        "base_model": os.getenv("FINE_TUNE_BASE_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        "method": os.getenv("FINE_TUNE_METHOD", "lora"),  # lora | qlora | full
        "lora_r": int(os.getenv("FINE_TUNE_R", "16")),
        "lora_alpha": int(os.getenv("FINE_TUNE_ALPHA", "32")),
        "lora_dropout": float(os.getenv("FINE_TUNE_DROPOUT", "0.1")),
        "batch_size": int(os.getenv("FINE_TUNE_BATCH_SIZE", "4")),
        "epochs": int(os.getenv("FINE_TUNE_EPOCHS", "3")),
        "learning_rate": float(os.getenv("FINE_TUNE_LEARNING_RATE", "2e-4")),
        "output_dir": os.getenv("FINE_TUNE_OUTPUT_DIR", "/app/fine-tune/output"),
        "dataset_source": os.getenv("FINE_TUNE_DATASET_SOURCE", "knowledge_base"),
        "dataset_path": "/app/fine-tune/datasets/training.jsonl",
    }


def check_gpu() -> dict[str, Any]:
    """Check GPU availability and capabilities."""
    info = {
        "available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "device_name": "",
        "total_memory_gb": 0,
    }

    if info["available"]:
        info["device_name"] = torch.cuda.get_device_name(0)
        info["total_memory_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2)
        logger.info("GPU: %s (%s GB)", info["device_name"], info["total_memory_gb"])
    else:
        logger.warning("No GPU detected. Fine-tuning on CPU will be extremely slow.")

    return info


def try_unsloth(config: dict[str, Any]) -> bool:
    """Attempt to use Unsloth for fine-tuning.

    Returns True if successful.
    """
    try:
        from unsloth import FastLanguageModel, is_bfloat16_supported
        from unsloth.chat_templates import get_chat_template

        logger.info("Using Unsloth for optimized fine-tuning")

        # Load model with Unsloth
        max_seq_length = 4096
        dtype = torch.bfloat16 if is_bfloat16_supported() else torch.float16
        load_in_4bit = config["method"] == "qlora"

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=config["base_model"],
            max_seq_length=max_seq_length,
            dtype=dtype,
            load_in_4bit=load_in_4bit,
        )

        # Apply LoRA
        model = FastLanguageModel.get_peft_model(
            model,
            r=config["lora_r"],
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                           "gate_proj", "up_proj", "down_proj"],
            lora_alpha=config["lora_alpha"],
            lora_dropout=config["lora_dropout"],
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=42,
            use_rslora=False,
            loftq_config=None,
        )

        # Load dataset
        from dataset import load_dataset
        samples = load_dataset(
            config["dataset_path"],
            max_samples=0,
            format="alpaca",
        )

        if not samples:
            logger.error("No training samples found")
            return False

        # Tokenize
        from datasets import Dataset as HFDataset
        hf_dataset = HFDataset.from_list(samples)

        def tokenize_fn(examples):
            texts = examples["text"]
            encodings = tokenizer(texts, truncation=True, padding="max_length",
                                  max_length=max_seq_length)
            encodings["labels"] = encodings["input_ids"].copy()
            return encodings

        tokenized = hf_dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

        # Trainer
        from trl import SFTTrainer
        from transformers import TrainingArguments

        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=tokenized,
            dataset_text_field="text",
            max_seq_length=max_seq_length,
            dataset_num_proc=2,
            packing=False,
            args=TrainingArguments(
                per_device_train_batch_size=config["batch_size"],
                gradient_accumulation_steps=4,
                warmup_steps=5,
                num_train_epochs=config["epochs"],
                learning_rate=config["learning_rate"],
                fp16=not is_bfloat16_supported(),
                bf16=is_bfloat16_supported(),
                logging_steps=1,
                optim="adamw_8bit",
                weight_decay=0.01,
                lr_scheduler_type="linear",
                seed=42,
                output_dir=config["output_dir"],
                report_to="none",
                save_strategy="epoch",
            ),
        )

        # Train
        logger.info("Starting Unsloth training...")
        trainer.train()

        # Save
        output_path = Path(config["output_dir"]) / "lora_model"
        model.save_pretrained(str(output_path))
        tokenizer.save_pretrained(str(output_path))
        logger.info("Model saved to %s", output_path)

        # Save merged model
        merged_path = Path(config["output_dir"]) / "merged_model"
        model.save_pretrained_merged(str(merged_path), tokenizer, save_method="merged_16bit")
        logger.info("Merged model saved to %s", merged_path)

        return True

    except ImportError:
        logger.info("Unsloth not available, falling back to vanilla PEFT")
        return False
    except Exception as e:
        logger.error("Unsloth training failed: %s", str(e))
        return False


def try_vanilla_peft(config: dict[str, Any]) -> bool:
    """Fallback: Use vanilla PEFT/LoRA without Unsloth."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from peft import LoraConfig, get_peft_model, TaskType
        from trl import SFTTrainer
        from datasets import Dataset as HFDataset

        logger.info("Using vanilla PEFT for fine-tuning")

        # Load model
        model_name = config["base_model"]
        use_4bit = config["method"] == "qlora"

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
            load_in_4bit=use_4bit,
            device_map="auto",
            trust_remote_code=True,
        )

        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        if config["method"] != "full":
            # LoRA config
            peft_config = LoraConfig(
                r=config["lora_r"],
                lora_alpha=config["lora_alpha"],
                lora_dropout=config["lora_dropout"],
                bias="none",
                task_type=TaskType.CAUSAL_LM,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            )
            model = get_peft_model(model, peft_config)

        # Load dataset
        from dataset import load_dataset
        samples = load_dataset(
            config["dataset_path"],
            max_samples=0,
            format="alpaca",
        )
        if not samples:
            logger.error("No training samples found")
            return False

        # Tokenize
        def tokenize_fn(examples):
            texts = examples["text"]
            encodings = tokenizer(texts, truncation=True, padding="max_length",
                                  max_length=2048)
            encodings["labels"] = encodings["input_ids"].copy()
            return encodings

        hf_dataset = HFDataset.from_list(samples)
        tokenized = hf_dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

        # Training arguments
        args = TrainingArguments(
            output_dir=config["output_dir"],
            per_device_train_batch_size=config["batch_size"],
            gradient_accumulation_steps=4,
            warmup_steps=10,
            num_train_epochs=config["epochs"],
            learning_rate=config["learning_rate"],
            bf16=torch.cuda.is_bf16_supported(),
            fp16=not torch.cuda.is_bf16_supported(),
            logging_steps=10,
            save_strategy="epoch",
            report_to="none",
            save_total_limit=2,
            remove_unused_columns=False,
            optim="adamw_torch",
        )

        # Trainer
        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            args=args,
            train_dataset=tokenized,
            max_seq_length=2048,
        )

        # Train
        logger.info("Starting PEFT training...")
        trainer.train()

        # Save adapter
        model.save_pretrained(f"{config['output_dir']}/peft_adapter")
        tokenizer.save_pretrained(f"{config['output_dir']}/peft_adapter")
        logger.info("Adapter saved to %s/output/peft_adapter", config["output_dir"])

        return True

    except Exception as e:
        logger.error("PEFT training failed: %s", str(e))
        return False


def list_datasets():
    """List available datasets."""
    from dataset import list_datasets as _list_datasets
    datasets = _list_datasets()
    if not datasets:
        print("No datasets found in /app/datasets/")
        print("Run 'make fine-tune-collect' first to generate training data.")
        return

    print(f"\n{'Dataset':<30} {'Size':>10}")
    print("-" * 42)
    for d in datasets:
        print(f"{d['name']:<30} {d['size_mb']:>8.2f} MB")


def main():
    """Main entry point."""
    import fire
    fire.Fire({
        "train": train,
        "list-datasets": list_datasets,
        "check-gpu": check_gpu,
    })


def train(
    base_model: str = "",
    dataset: str = "",
    method: str = "",
    epochs: int = 0,
    batch_size: int = 0,
    learning_rate: float = 0.0,
    lora_r: int = 0,
):
    """Run fine-tuning with the given or environment-based configuration."""
    config = get_env_config()

    # CLI overrides
    if base_model:
        config["base_model"] = base_model
    if dataset:
        config["dataset_path"] = dataset
    if method:
        config["method"] = method
    if epochs > 0:
        config["epochs"] = epochs
    if batch_size > 0:
        config["batch_size"] = batch_size
    if learning_rate > 0:
        config["learning_rate"] = learning_rate
    if lora_r > 0:
        config["lora_r"] = lora_r

    gpu_info = check_gpu()
    if not gpu_info["available"]:
        logger.warning("Continuing without GPU (will be very slow)")

    logger.info("Fine-tuning config: %s", json.dumps(config, indent=2, ensure_ascii=False))

    # Try Unsloth first, fall back to vanilla PEFT
    start_time = time.time()
    success = try_unsloth(config)
    if not success:
        success = try_vanilla_peft(config)

    elapsed = time.time() - start_time
    if success:
        logger.info("Training completed in %.2f minutes", elapsed / 60)
        # Save training summary
        summary = {
            "status": "completed",
            "config": config,
            "elapsed_seconds": elapsed,
            "gpu": gpu_info,
        }
        with open(f"{config['output_dir']}/training_summary.json", "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    else:
        logger.error("Training failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
