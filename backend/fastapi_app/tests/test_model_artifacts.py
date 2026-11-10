"""
Unit Tests for Model Artifacts, Missing File Handling, and Training Integrity
"""

import os
import sys
import tempfile
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.fine_tuning.train_qwen import (
    load_training_config,
    train_qwen_lora,
    find_latest_checkpoint,
    get_system_hardware_details,
)


def test_load_training_config_defaults_and_override():
    # Built-in fallback
    cfg = load_training_config("nonexistent_path.yaml")
    assert "model" in cfg
    assert cfg["model"]["base_model"] == "Qwen/Qwen2.5-1.5B-Instruct"
    assert "lora" in cfg
    assert cfg["lora"]["r"] == 16
    assert "training" in cfg


def test_dry_run_never_reports_completed_training():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = train_qwen_lora(dry_run=True)
        # Training integrity assertion: A dry-run MUST NOT report trained: True or status: "completed"
        assert res["status"] == "dry_run"
        assert res["trained"] is False
        assert "message" in res
        assert "No GPU training was executed" in res["message"]


def test_missing_dataset_dry_run_error():
    res = train_qwen_lora(dataset_path="nonexistent_dataset.jsonl", dry_run=True)
    assert res["status"] == "dry_run_error"
    assert res["trained"] is False
    assert "not found" in res["error"]


def test_gpu_enforcement_prevents_local_cpu_crash():
    hw = get_system_hardware_details()
    if not hw["cuda_available"]:
        # When CUDA is not available and dry_run is False, train_qwen_lora must raise RuntimeError
        # preventing loading 1.5B weights onto the 8 GB RAM laptop
        with pytest.raises(RuntimeError) as exc_info:
            train_qwen_lora(dry_run=False, cpu_smoke_test=False)
        assert "Genuine fine-tuning requires an NVIDIA GPU with CUDA" in str(exc_info.value)
        assert "Google Colab" in str(exc_info.value)


def test_find_latest_checkpoint():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert find_latest_checkpoint(tmpdir) is None

        # Create dummy checkpoint dirs
        cp1 = os.path.join(tmpdir, "checkpoint-10")
        cp2 = os.path.join(tmpdir, "checkpoint-50")
        cp3 = os.path.join(tmpdir, "checkpoint-25")
        for cp in [cp1, cp2, cp3]:
            os.makedirs(cp)

        latest = find_latest_checkpoint(tmpdir)
        assert latest == cp2
