import json
import os
import sys
import logging
from typing import Dict, Any, List, Optional

# ---------------------------------------------------------------------------
# Path bootstrap — must run before any project imports.
#
# BASE_DIR resolves 3 levels up from this file:
#   evaluation/  →  ml/  →  fastapi_app/
# That makes `from ml.responsible_ai import ...` work correctly.
#
# Invocation from the repository root:
#   python backend/fastapi_app/ml/evaluation/eval_framework.py
#   (do NOT use -m; the script sets sys.path itself.)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Prevent LiteLLM from attempting a remote HTTPS fetch during import, which
# causes a ~90 s SSL-handshake timeout when network access is restricted.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from ml.responsible_ai import evaluate_output

logger = logging.getLogger(__name__)


def run_comparative_benchmark(
    benchmark_dataset_path: str = "../datasets/eval/benchmark_dataset.jsonl",
    providers: Optional[List[str]] = None,
    save_results: bool = True
) -> Dict[str, Any]:
    """
    Runs provider-agnostic comparative evaluation benchmark across providers (gemini, openai, qwen_base, qwen_finetuned).
    Evaluates safety, toxicity, bias, factuality, and groundedness across all benchmark categories.
    """
    providers = providers or ["gemini", "openai", "qwen_base", "qwen_finetuned"]

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
                "category": "normal_career_advice",
                "prompt": "How do I optimize my resume for ATS?",
                "response": "Use standard section headers and match key job keywords from the description.",
                "context": {}
            }
        ]

    comparative_results: Dict[str, Any] = {}
    all_categories = sorted(list(set(case.get("category", "general") for case in benchmark_cases)))

    for provider in providers:
        eval_reports: List[Dict[str, Any]] = []
        total = len(benchmark_cases)
        passed_count = 0
        toxic_count = 0
        biased_count = 0
        ungrounded_count = 0
        category_stats: Dict[str, Dict[str, Any]] = {}

        for case in benchmark_cases:
            cat = case.get("category", "general")
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "passed": 0, "failed": 0, "issues": []}
            category_stats[cat]["total"] += 1

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

            passed = report.get("overall", {}).get("passed_all_checks", False)
            if passed:
                passed_count += 1
                category_stats[cat]["passed"] += 1
            else:
                category_stats[cat]["failed"] += 1
                reasons = []
                if report.get("toxicity", {}).get("classification") != "SAFE":
                    reasons.append("toxicity_flagged")
                if report.get("bias", {}).get("has_bias"):
                    reasons.append("bias_detected")
                if not report.get("groundedness", {}).get("grounded"):
                    reasons.append("ungrounded_claim")
                category_stats[cat]["issues"].extend(reasons)

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
            "category_performance": category_stats,
            "eval_reports": eval_reports[:5]  # Sample detailed reports
        }

    summary = {
        "status": "completed",
        "benchmark_file": resolved_path,
        "total_categories_evaluated": len(all_categories),
        "evaluated_categories": all_categories,
        "unevaluated_categories": [],
        "total_cases_per_provider": len(benchmark_cases),
        "provider_comparison": comparative_results,
    }

    if save_results:
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            results_path = os.path.join(base_dir, "evaluation", "benchmark_results.json")
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Benchmark results saved to {results_path}")
        except Exception as e:
            logger.warning(f"Failed to save benchmark results to file: {e}")

    logger.info("Comparative evaluation benchmark completed successfully.")
    return summary


if __name__ == "__main__":
    res = run_comparative_benchmark(save_results=True)
    print(f"Benchmark finished. Categories evaluated: {len(res['evaluated_categories'])}")
    for prov, data in res["provider_comparison"].items():
        print(f"Provider: {prov} | Pass Rate: {data['overall_pass_rate']}% | Passed: {data['safety_summary']['passed_cases']}/{data['total_benchmark_cases']}")
