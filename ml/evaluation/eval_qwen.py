"""
CareerOS Qwen Evaluation CLI & Interface
-----------------------------------------
Coordinates evaluation of Fine-Tuned Qwen, Base Qwen, and Gemini models.
Provides unified summary metrics and triggers 3-way benchmarking.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.evaluation.benchmark_runner import run_three_way_benchmark

logger = logging.getLogger(__name__)


def evaluate_qwen_model(
    eval_dataset_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    adapter_path: Optional[str] = None,
    local_safe_mode: bool = True
) -> Dict[str, Any]:
    """
    Evaluates Qwen fine-tuned & base models alongside Gemini 2.5 Flash.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    resolved_output_dir = output_dir or os.path.join(script_dir, "outputs")
    resolved_adapter_path = adapter_path or os.path.join(
        os.path.dirname(os.path.dirname(script_dir)), "models", "qwen_career_lora"
    )

    benchmark_report = run_three_way_benchmark(
        benchmark_dataset_path=eval_dataset_path,
        output_dir=resolved_output_dir,
        gemini_api_key=gemini_api_key,
        adapter_path=resolved_adapter_path,
        local_safe_mode=local_safe_mode
    )

    qwen_ft = benchmark_report.get("summary", {}).get("qwen_finetuned", {})

    return {
        "status": "completed",
        "model": "Qwen-FineTuned",
        "total_test_cases": qwen_ft.get("total_evaluated_cases", 0),
        "safety_compliance_rate": qwen_ft.get("safety_pass_rate", 100.0),
        "avg_latency_ms": qwen_ft.get("avg_latency_ms", 0.0),
        "avg_rouge_l_f1": qwen_ft.get("avg_rouge_l_f1", 0.0),
        "comparative_summary": benchmark_report.get("summary", {}),
        "outputs_directory": resolved_output_dir
    }


if __name__ == "__main__":
    res = evaluate_qwen_model()
    print("\n=== QWEN EVALUATION RUN COMPLETE ===")
    print("Total Cases Evaluated:", res["total_test_cases"])
    for m_key, summary in res["comparative_summary"].items():
        print(f"Model: {summary['model_name']} | Latency: {summary['avg_latency_ms']}ms | ROUGE-L F1: {summary['avg_rouge_l_f1']} | Safety Pass: {summary['safety_pass_rate']}%")
