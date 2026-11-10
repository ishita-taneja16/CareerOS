"""
CareerOS Qwen2.5-1.5B-Instruct Supervised Fine-Tuning Pipeline
--------------------------------------------------------------
Implements parameter-efficient fine-tuning (PEFT LoRA / QLoRA) on career instruction datasets.
Configured for Google Colab GPU execution with automatic fallback and strict distinction
between dry-run validation and genuine completed training.
"""

import os
import sys
import json
import yaml
import time
import logging
import argparse
import platform
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("train_qwen")


def load_training_config(config_path: str) -> Dict[str, Any]:
    """Loads training configuration from YAML file with default fallbacks."""
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found at {config_path}. Using built-in defaults.")
        return {
            "model": {
                "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
                "model_revision": "main",
                "output_dir": "./checkpoints/qwen_career_lora",
                "max_seq_length": 512,
            },
            "lora": {
                "r": 16,
                "lora_alpha": 32,
                "lora_dropout": 0.05,
                "bias": "none",
                "task_type": "CAUSAL_LM",
                "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            },
            "training": {
                "per_device_train_batch_size": 2,
                "per_device_eval_batch_size": 2,
                "gradient_accumulation_steps": 4,
                "learning_rate": 2e-4,
                "num_train_epochs": 3,
                "warmup_ratio": 0.05,
                "lr_scheduler_type": "cosine",
                "logging_steps": 5,
                "save_strategy": "epoch",
                "eval_strategy": "epoch",
                "save_total_limit": 2,
                "fp16": True,
                "bf16": False,
                "gradient_checkpointing": True,
                "optim": "paged_adamw_8bit",
                "seed": 42,
            }
        }

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_system_hardware_details() -> Dict[str, Any]:
    """Inspects host system hardware, OS, and GPU availability."""
    details = {
        "os": platform.platform(),
        "python_version": sys.version.split()[0],
        "processor": platform.processor(),
        "cuda_available": False,
        "device_count": 0,
        "gpu_name": None,
        "gpu_vram_gb": 0.0,
        "qlora_supported": False,
    }

    try:
        import torch
        details["cuda_available"] = torch.cuda.is_available()
        if details["cuda_available"]:
            details["device_count"] = torch.cuda.device_count()
            details["gpu_name"] = torch.cuda.get_device_name(0)
            details["gpu_vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
            try:
                import bitsandbytes
                details["qlora_supported"] = True
            except ImportError:
                details["qlora_supported"] = False
    except ImportError:
        pass

    return details


def compute_file_hash(filepath: str) -> str:
    """Computes SHA-256 hash for dataset provenance."""
    if not os.path.exists(filepath):
        return "not_found"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def find_latest_checkpoint(output_dir: str) -> Optional[str]:
    """Finds latest HuggingFace checkpoint directory in output_dir."""
    if not os.path.isdir(output_dir):
        return None

    checkpoints = [
        os.path.join(output_dir, d) for d in os.listdir(output_dir)
        if d.startswith("checkpoint-") and os.path.isdir(os.path.join(output_dir, d))
    ]
    if not checkpoints:
        return None

    def step_num(path: str) -> int:
        try:
            return int(os.path.basename(path).split("-")[1])
        except (IndexError, ValueError):
            return 0

    return max(checkpoints, key=step_num)


def train_qwen_lora(
    config_path: str = "qwen_config.yaml",
    dataset_path: Optional[str] = None,
    val_dataset_path: Optional[str] = None,
    dry_run: bool = False,
    resume: bool = False,
    cpu_smoke_test: bool = False
) -> Dict[str, Any]:
    """
    Executes supervised fine-tuning of Qwen2.5-1.5B-Instruct using PEFT LoRA or QLoRA.
    Configured for Google Colab GPU execution.
    """
    start_time = time.time()
    timestamp = datetime.now(timezone.utc).isoformat()

    # Resolve paths relative to script location if needed
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(config_path) and not os.path.exists(config_path):
        resolved_config = os.path.join(script_dir, config_path)
        if os.path.exists(resolved_config):
            config_path = resolved_config

    config = load_training_config(config_path)
    model_cfg = config.get("model", {})
    lora_cfg = config.get("lora", {})
    train_cfg = config.get("training", {})

    output_dir = model_cfg.get("output_dir", "./checkpoints/qwen_career_lora")
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(script_dir, output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Resolve dataset paths
    if dataset_path is None:
        dataset_path = os.path.join(os.path.dirname(script_dir), "datasets", "train", "career_instructions_train.jsonl")
        if not os.path.exists(dataset_path):
            dataset_path = os.path.join(os.path.dirname(script_dir), "datasets", "train", "career_instructions.jsonl")

    if val_dataset_path is None:
        val_dataset_path = os.path.join(os.path.dirname(script_dir), "datasets", "train", "career_instructions_val.jsonl")

    hw_info = get_system_hardware_details()
    dataset_hash = compute_file_hash(dataset_path)

    # ── DRY-RUN / CI VALIDATION MODE ──────────────────────────────────────────
    if dry_run or os.environ.get("CI"):
        logger.info("Executing fine-tuning DRY-RUN validation mode.")
        if not os.path.exists(dataset_path):
            return {
                "status": "dry_run_error",
                "trained": False,
                "error": f"Training dataset not found at {dataset_path}",
                "timestamp": timestamp,
            }

        sample_count = 0
        with open(dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    sample_count += 1

        dry_run_summary = {
            "status": "dry_run",
            "trained": False,
            "message": "Fine-tuning configuration and dataset validated successfully. No GPU training was executed.",
            "timestamp": timestamp,
            "target_model": model_cfg.get("base_model", "Qwen/Qwen2.5-1.5B-Instruct"),
            "dataset": {
                "path": dataset_path,
                "sha256": dataset_hash,
                "sample_count": sample_count,
            },
            "output_directory": output_dir,
            "hardware_detected": hw_info,
            "lora_parameters": lora_cfg,
            "training_parameters": train_cfg,
        }

        # Save validated configuration to output dir
        saved_config_path = os.path.join(output_dir, "training_config.yaml")
        with open(saved_config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False)

        # Save dry-run metrics metadata
        dry_run_metrics_path = os.path.join(output_dir, "training_metrics.json")
        with open(dry_run_metrics_path, "w", encoding="utf-8") as f:
            json.dump(dry_run_summary, f, indent=2)

        return dry_run_summary

    # ── GENUINE TRAINING EXECUTION ────────────────────────────────────────────
    if not hw_info["cuda_available"] and not cpu_smoke_test:
        raise RuntimeError(
            "Genuine fine-tuning requires an NVIDIA GPU with CUDA. "
            "Local environment has integrated graphics / CPU only with 8 GB RAM. "
            "Please run notebooks/qwen_finetuning_colab.ipynb on Google Colab GPU to execute training. "
            "To validate configuration locally without training, use --dry-run."
        )

    logger.info("Importing PyTorch, Transformers, and PEFT for fine-tuning...")
    import torch
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        TrainingArguments,
        Trainer,
        DataCollatorForSeq2Seq,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    base_model_name = model_cfg.get("base_model", "Qwen/Qwen2.5-1.5B-Instruct")
    logger.info(f"Loading tokenizer for {base_model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Setup quantization & precision
    use_qlora = hw_info["qlora_supported"] and hw_info["cuda_available"]
    logger.info(f"QLoRA 4-bit support: {use_qlora}")

    model_kwargs = {"trust_remote_code": True}
    if use_qlora:
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model_kwargs["quantization_config"] = bnb_config
        model_kwargs["device_map"] = "auto"
    elif hw_info["cuda_available"]:
        model_kwargs["torch_dtype"] = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        model_kwargs["device_map"] = "auto"
    else:
        # CPU smoke test mode
        model_kwargs["torch_dtype"] = torch.float32

    logger.info(f"Loading base model {base_model_name}...")
    model = AutoModelForCausalLM.from_pretrained(base_model_name, **model_kwargs)

    if use_qlora:
        model = prepare_model_for_kbit_training(model)

    # PEFT LoRA Config
    peft_config = LoraConfig(
        r=lora_cfg.get("r", 16),
        lora_alpha=lora_cfg.get("lora_alpha", 32),
        lora_dropout=lora_cfg.get("lora_dropout", 0.05),
        bias=lora_cfg.get("bias", "none"),
        task_type=lora_cfg.get("task_type", "CAUSAL_LM"),
        target_modules=lora_cfg.get("target_modules", ["q_proj", "k_proj", "v_proj", "o_proj"]),
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Load and tokenize dataset
    def parse_jsonl(path: str) -> List[Dict[str, Any]]:
        items = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
        return items

    raw_train = parse_jsonl(dataset_path)
    raw_val = parse_jsonl(val_dataset_path) if os.path.exists(val_dataset_path) else []

    max_seq_len = model_cfg.get("max_seq_length", 512)

    def tokenize_sample(item: Dict[str, Any]) -> Dict[str, Any]:
        if "messages" in item:
            text = tokenizer.apply_chat_template(item["messages"], tokenize=False, add_generation_prompt=False)
        else:
            inst = item.get("instruction", "")
            inp = item.get("input", "")
            out = item.get("output", "")
            prompt = f"{inst}\n\n{inp}" if inp else inst
            messages = [
                {"role": "system", "content": "You are CareerOS, an expert AI career co-pilot."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": out}
            ]
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)

        encoded = tokenizer(text, max_length=max_seq_len, truncation=True, padding=False)
        encoded["labels"] = list(encoded["input_ids"])
        return encoded

    train_tokenized = [tokenize_sample(x) for x in raw_train]
    val_tokenized = [tokenize_sample(x) for x in raw_val] if raw_val else None

    # Hugging Face Training Arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=train_cfg.get("per_device_train_batch_size", 2),
        per_device_eval_batch_size=train_cfg.get("per_device_eval_batch_size", 2),
        gradient_accumulation_steps=train_cfg.get("gradient_accumulation_steps", 4),
        learning_rate=float(train_cfg.get("learning_rate", 2e-4)),
        num_train_epochs=train_cfg.get("num_train_epochs", 3) if not cpu_smoke_test else 0.05,
        max_steps=1 if cpu_smoke_test else -1,
        warmup_ratio=train_cfg.get("warmup_ratio", 0.05),
        lr_scheduler_type=train_cfg.get("lr_scheduler_type", "cosine"),
        logging_steps=train_cfg.get("logging_steps", 5),
        save_strategy=train_cfg.get("save_strategy", "epoch"),
        eval_strategy=train_cfg.get("eval_strategy", "epoch") if val_tokenized else "no",
        save_total_limit=train_cfg.get("save_total_limit", 2),
        fp16=train_cfg.get("fp16", True) and hw_info["cuda_available"],
        bf16=train_cfg.get("bf16", False) and hw_info["cuda_available"],
        gradient_checkpointing=train_cfg.get("gradient_checkpointing", True) and hw_info["cuda_available"],
        optim=train_cfg.get("optim", "paged_adamw_8bit") if use_qlora else "adamw_torch",
        seed=train_cfg.get("seed", 42),
        report_to="none",
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8, return_tensors="pt", padding=True)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tokenized,
        eval_dataset=val_tokenized,
        data_collator=data_collator,
    )

    # Check for resuming interrupted training
    resume_checkpoint = None
    if resume:
        resume_checkpoint = find_latest_checkpoint(output_dir)
        if resume_checkpoint:
            logger.info(f"Resuming training from checkpoint: {resume_checkpoint}")
        else:
            logger.info("No checkpoint found to resume from. Starting from scratch.")

    logger.info("Commencing supervised fine-tuning loop...")
    train_result = trainer.train(resume_from_checkpoint=resume_checkpoint)
    training_duration_sec = round(time.time() - start_time, 2)

    # Save LoRA adapter weights and tokenizer files
    logger.info(f"Saving fine-tuned adapter and tokenizer to {output_dir}...")
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Extract loss history
    loss_history = []
    for log in trainer.state.log_history:
        if "loss" in log or "eval_loss" in log:
            loss_history.append(log)

    metrics_summary = {
        "status": "completed",
        "trained": True,
        "run_timestamp": timestamp,
        "base_model": base_model_name,
        "model_revision": model_cfg.get("model_revision", "main"),
        "dataset_hash": dataset_hash,
        "train_samples": len(train_tokenized),
        "val_samples": len(val_tokenized) if val_tokenized else 0,
        "training_duration_seconds": training_duration_sec,
        "train_loss": train_result.training_loss if hasattr(train_result, "training_loss") else None,
        "loss_history": loss_history,
        "hardware_details": hw_info,
        "hyperparameters": {
            "r": lora_cfg.get("r", 16),
            "lora_alpha": lora_cfg.get("lora_alpha", 32),
            "learning_rate": train_cfg.get("learning_rate", 2e-4),
            "batch_size": train_cfg.get("per_device_train_batch_size", 2),
            "gradient_accumulation_steps": train_cfg.get("gradient_accumulation_steps", 4),
            "epochs": train_cfg.get("num_train_epochs", 3),
            "max_seq_length": max_seq_len,
        }
    }

    # Save training_metrics.json
    metrics_path = os.path.join(output_dir, "training_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    # Save training_config.yaml
    config_save_path = os.path.join(output_dir, "training_config.yaml")
    with open(config_save_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)

    logger.info(f"Fine-tuning completed successfully in {training_duration_sec}s. Metrics saved to {metrics_path}")
    return metrics_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CareerOS Qwen Fine-Tuning CLI")
    parser.add_argument("--config", type=str, default="qwen_config.yaml", help="Path to config YAML")
    parser.add_argument("--dataset", type=str, default=None, help="Path to training dataset JSONL")
    parser.add_argument("--val-dataset", type=str, default=None, help="Path to validation dataset JSONL")
    parser.add_argument("--dry-run", action="store_true", help="Run configuration validation without GPU training")
    parser.add_argument("--resume", action="store_true", help="Resume from latest checkpoint if available")
    parser.add_argument("--cpu-smoke-test", action="store_true", help="Run 1-step CPU smoke test (testing only)")

    args = parser.parse_args()

    result = train_qwen_lora(
        config_path=args.config,
        dataset_path=args.dataset,
        val_dataset_path=args.val_dataset,
        dry_run=args.dry_run,
        resume=args.resume,
        cpu_smoke_test=args.cpu_smoke_test,
    )

    print("\n=== FINE-TUNING EXECUTION RESULT ===")
    print(json.dumps(result, indent=2))
