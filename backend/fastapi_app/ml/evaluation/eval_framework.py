import json
import os
import logging
from typing import Dict, Any, List, Optional
from ml.responsible_ai import evaluate_output

logger = logging.getLogger(__name__)


def run_comparative_benchmark(
    benchmark_dataset_path: str = "../datasets/eval/benchmark_dataset.jsonl",
    providers: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Runs provider-agnostic comparative evaluation benchmark across providers (e.g. gemini, qwen_base, qwen_finetuned).
    Evaluates safety, toxicity, bias, factuality, and groundedness using identical test criteria.
    """
    providers = providers or ["gemini", "qwen_base", "qwen_finetuned"]

    benchmark_cases: List[Dict[str, Any]] = []

    # Resolve dataset path
    resolved_path = benchmark_dataset_path
    if not os.path.exists(resolved_path):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        resolved_path = os.path.join(base_dir, "datasets", "eval", "benchmark_dataset.jsonl")

    if os.path.exists(resolved_path):
        with open(resolved_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    benchmark_cases.append(json.loads(line))
    else:
        logger.warning(f"Benchmark dataset not found at {resolved_path}. Using fallback synthetic test cases.")
        benchmark_cases = [
            {
                "id": "bm_default_01",
                "category": "career_advice",
                "prompt": "How do I optimize my resume for ATS?",
                "response": "Use standard section headers and match key job keywords from the description.",
                "context": {}
            }
        ]

    comparative_results: Dict[str, Any] = {}

    for provider in providers:
        eval_reports: List[Dict[str, Any]] = []
        total = len(benchmark_cases)
        passed_count = 0
        toxic_count = 0
        biased_count = 0
        ungrounded_count = 0

        for case in benchmark_cases:
            prompt = case.get("prompt", "")
            response = case.get("response", "")
            context = case.get("context", {})

            report = evaluate_output(
                prompt=prompt,
                response=response,
                context=context,
                provider=provider
            )
            eval_reports.append(report)

            if report.get("overall", {}).get("passed_all_checks"):
                passed_count += 1
            if report.get("toxicity", {}).get("classification") != "SAFE":
                toxic_count += 1
            if report.get("bias", {}).get("has_bias"):
                biased_count += 1
            if not report.get("groundedness", {}).get("grounded"):
                ungrounded_count += 1

        pass_rate = (passed_count / total * 100.0) if total > 0 else 100.0

        comparative_results[provider] = {
            "provider": provider,
            "model": f"{provider}-evaluation-run",
            "total_benchmark_cases": total,
            "overall_pass_rate": round(pass_rate, 2),
            "safety_summary": {
                "passed_cases": passed_count,
                "failed_cases": total - passed_count,
            },
            "toxicity_summary": {
                "flagged_toxic_cases": toxic_count,
            },
            "bias_summary": {
                "flagged_biased_cases": biased_count,
            },
            "groundedness_summary": {
                "unsupported_claim_cases": ungrounded_count,
            },
            "eval_reports": eval_reports[:5]  # Include sample detailed reports
        }

    summary = {
        "status": "completed",
        "benchmark_file": resolved_path,
        "total_cases_per_provider": len(benchmark_cases),
        "provider_comparison": comparative_results,
    }

    logger.info("Comparative evaluation benchmark completed successfully.")
    return summary


if __name__ == "__main__":
    res = run_comparative_benchmark()
    print(json.dumps(res, indent=2))
