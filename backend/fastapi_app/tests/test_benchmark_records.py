"""
Unit Tests for Benchmark Record Validation, Aggregation, and Export
"""

import os
import sys
import tempfile
import csv
import json
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.evaluation.benchmark_runner import (
    load_held_out_benchmark_cases,
    run_three_way_benchmark,
    BenchmarkInferenceProvider,
    get_environment_info,
)


def test_environment_info_structure():
    env = get_environment_info()
    assert "os" in env
    assert "python_version" in env
    assert "cuda_available" in env
    assert "packages" in env
    assert isinstance(env["packages"], dict)


def test_load_held_out_benchmark_cases():
    cases = load_held_out_benchmark_cases()
    assert len(cases) > 0
    first = cases[0]
    assert "id" in first
    assert "prompt" in first
    assert "response" in first
    assert "category" in first


def test_benchmark_inference_provider_local_safe_mode():
    provider = BenchmarkInferenceProvider(
        gemini_api_key="",
        adapter_path="./nonexistent_adapter",
        local_safe_mode=True
    )

    # Base Qwen should not crash or load 1.5B model on 8 GB RAM local laptop
    base_res = provider.call_base_qwen("Test prompt")
    assert base_res["mode"] == "local_safe_simulated"
    assert "prompt_tokens" in base_res
    assert "completion_tokens" in base_res
    assert "latency_ms" in base_res

    # Missing Gemini key returns graceful error record, does not raise unhandled exception
    gemini_res = provider.call_gemini("Test prompt")
    assert gemini_res["error"] == "MISSING_GEMINI_API_KEY"
    assert gemini_res["mode"] == "skipped_no_key"

    # Missing adapter path returns graceful error record
    ft_res = provider.call_ft_qwen("Test prompt")
    assert "MISSING_ADAPTER" in str(ft_res.get("error"))


def test_run_three_way_benchmark_pipeline():
    with tempfile.TemporaryDirectory() as tmpdir:
        report = run_three_way_benchmark(
            output_dir=tmpdir,
            local_safe_mode=True,
            max_cases=2
        )

        assert "benchmark_metadata" in report
        assert "summary" in report
        assert "cases" in report
        assert len(report["cases"]) == 2

        # Check summary for all 3 models
        summary = report["summary"]
        assert "gemini_2_5_flash" in summary
        assert "qwen_base" in summary
        assert "qwen_finetuned" in summary

        # Verify output files exist
        json_file = os.path.join(tmpdir, "benchmark_results.json")
        csv_file = os.path.join(tmpdir, "benchmark_results.csv")
        md_file = os.path.join(tmpdir, "model_comparison.md")

        assert os.path.exists(json_file)
        assert os.path.exists(csv_file)
        assert os.path.exists(md_file)

        # Validate CSV contents
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # 2 cases * 3 models = 6 rows
            assert len(rows) == 6
            assert "latency_ms" in rows[0]
            assert "rouge_l_f1" in rows[0]
            assert "safety_verdict" in rows[0]
