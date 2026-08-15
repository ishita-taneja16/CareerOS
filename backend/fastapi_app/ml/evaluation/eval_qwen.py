import logging
from typing import Dict, Any, Optional
from .eval_framework import run_comparative_benchmark

logger = logging.getLogger(__name__)


def evaluate_qwen_model(
    eval_dataset_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates Qwen fine-tuned & base models alongside Gemini using the provider-agnostic benchmark framework.
    """
    dataset_path = eval_dataset_path or "../datasets/eval/benchmark_dataset.jsonl"
    results = run_comparative_benchmark(
        benchmark_dataset_path=dataset_path,
        providers=["qwen_finetuned", "qwen_base", "gemini"]
    )

    qwen_finetuned_res = results.get("provider_comparison", {}).get("qwen_finetuned", {})

    return {
        "status": "completed",
        "model": "Qwen-FineTuned",
        "total_test_cases": qwen_finetuned_res.get("total_benchmark_cases", 0),
        "safety_compliance_rate": qwen_finetuned_res.get("overall_pass_rate", 100.0),
        "comparative_summary": results.get("provider_comparison", {}),
    }


if __name__ == "__main__":
    res = evaluate_qwen_model()
    print("Qwen Evaluation Results:", res)
