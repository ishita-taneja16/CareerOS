"""
Unit Tests for CareerOS Dataset Splitting, Deduplication, and Leakage Prevention
"""

import os
import sys
import tempfile
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.datasets.dataset_builder import (
    validate_sample_schema,
    deduplicate_dataset,
    deterministic_split,
    check_train_test_leakage,
    to_chatml,
    build_and_save_dataset_splits,
    RAW_CAREER_DATASET,
)


def test_sample_schema_validation():
    valid = {
        "id": "test_001",
        "category": "technical_interview",
        "instruction": "Explain FastAPI concurrency.",
        "input": "Technical query",
        "output": "FastAPI uses ASGI and asyncio event loop."
    }
    assert validate_sample_schema(valid) is True

    invalid_missing_output = {
        "id": "test_002",
        "category": "technical_interview",
        "instruction": "Explain FastAPI concurrency.",
        "input": "Technical query",
        "output": "   "
    }
    assert validate_sample_schema(invalid_missing_output) is False


def test_dataset_deduplication():
    sample1 = {"id": "1", "category": "resume", "instruction": "Rewrite bullet", "input": "Did tests", "output": "Tested"}
    sample2 = {"id": "2", "category": "resume", "instruction": "Rewrite bullet", "input": "Did tests", "output": "Tested"}
    sample3 = {"id": "3", "category": "resume", "instruction": "Different", "input": "New", "output": "Output"}

    unique = deduplicate_dataset([sample1, sample2, sample3])
    assert len(unique) == 2
    assert unique[0]["id"] == "1"
    assert unique[1]["id"] == "3"


def test_deterministic_split_reproducibility():
    samples = [{"id": f"s_{i}", "category": "cat", "instruction": f"inst {i}", "output": f"out {i}"} for i in range(20)]

    train1, val1, test1 = deterministic_split(samples, train_ratio=0.8, val_ratio=0.1, seed=42)
    train2, val2, test2 = deterministic_split(samples, train_ratio=0.8, val_ratio=0.1, seed=42)

    assert [s["id"] for s in train1] == [s["id"] for s in train2]
    assert [s["id"] for s in val1] == [s["id"] for s in val2]
    assert [s["id"] for s in test1] == [s["id"] for s in test2]

    # Proportions check
    assert len(train1) == 16
    assert len(val1) == 2
    assert len(test1) == 2


def test_zero_train_test_leakage_detection():
    train = [{"id": "tr_1", "instruction": "How to optimize resume?", "input": ""}]
    test_clean = [{"id": "te_1", "instruction": "Explain Docker containers", "input": ""}]
    benchmark_clean = [{"id": "bm_1", "instruction": "Describe STAR method", "input": ""}]

    passed, warnings = check_train_test_leakage(train, test_clean, benchmark_clean)
    assert passed is True
    assert len(warnings) == 0

    # Introduce intentional leakage
    test_leaked = [{"id": "te_leaked", "instruction": "How to optimize resume?", "input": ""}]
    passed_leak, warnings_leak = check_train_test_leakage(train, test_leaked, benchmark_clean)
    assert passed_leak is False
    assert len(warnings_leak) == 1
    assert "LEAKAGE in test set" in warnings_leak[0]


def test_chatml_formatting():
    sample = {
        "id": "cml_01",
        "category": "interview",
        "instruction": "Explain GIL in Python.",
        "input": "Thread safety context",
        "output": "The Global Interpreter Lock prevents multiple native threads from executing Python bytecodes simultaneously."
    }
    chatml = to_chatml(sample)
    assert "messages" in chatml
    messages = chatml["messages"]
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Explain GIL in Python." in messages[1]["content"]
    assert "Thread safety context" in messages[1]["content"]
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == sample["output"]


def test_full_dataset_build_and_split_pipeline():
    with tempfile.TemporaryDirectory() as tmpdir:
        summary = build_and_save_dataset_splits(output_dir=tmpdir, seed=42)
        assert summary["leakage_check_passed"] is True
        assert summary["split_counts"]["train"] > 0
        assert summary["split_counts"]["test"] > 0
        assert "train" in summary["file_hashes_sha256"]
        assert os.path.exists(os.path.join(tmpdir, "career_instructions_train.jsonl"))
        assert os.path.exists(os.path.join(tmpdir, "dataset_split_summary.json"))
