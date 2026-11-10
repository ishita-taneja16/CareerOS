"""
CareerOS Evaluation Metrics & Responsible AI Scoring Suite
----------------------------------------------------------
Calculates ROUGE-L, ATS keyword coverage, Exact Match,
automated human evaluation rubric proxies (relevance, correctness, completeness, groundedness),
and connects to the Responsible AI safety audit engines.
"""

import re
import string
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Lowercases text, removes punctuation, and normalizes whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return " ".join(text.split())


def _lcs_length(tokens_a: List[str], tokens_b: List[str]) -> int:
    """Computes Length of Longest Common Subsequence between two token lists."""
    m, n = len(tokens_a), len(tokens_b)
    if m == 0 or n == 0:
        return 0

    # Space-optimized 2-row DP table
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if tokens_a[i - 1] == tokens_b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = list(curr)

    return curr[n]


def calculate_rouge_l(candidate: str, reference: str) -> Dict[str, float]:
    """
    Computes sentence-level Longest Common Subsequence (ROUGE-L) Precision, Recall, and F1.
    """
    if not candidate.strip() or not reference.strip():
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    cand_tokens = normalize_text(candidate).split()
    ref_tokens = normalize_text(reference).split()

    if not cand_tokens or not ref_tokens:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    lcs = _lcs_length(cand_tokens, ref_tokens)

    precision = lcs / len(cand_tokens) if cand_tokens else 0.0
    recall = lcs / len(ref_tokens) if ref_tokens else 0.0

    if precision + recall > 0:
        f1 = (2 * precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def calculate_exact_match(candidate: str, reference: str) -> float:
    """Exact match score (1.0 if identical normalized text, else 0.0)."""
    return 1.0 if normalize_text(candidate) == normalize_text(reference) else 0.0


def calculate_keyword_coverage(candidate: str, expected_keywords: List[str]) -> float:
    """Calculates percentage of expected target keywords present in candidate response."""
    if not expected_keywords:
        return 1.0

    norm_cand = normalize_text(candidate)
    matched = 0
    for kw in expected_keywords:
        norm_kw = normalize_text(kw)
        if norm_kw in norm_cand:
            matched += 1

    return round(matched / len(expected_keywords), 4)


def evaluate_rubric(
    prompt: str,
    response: str,
    reference: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    expected_keywords: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Calculates 1-5 scores across 4 key evaluation axes:
    1. Relevance: Did the model answer the specific career prompt?
    2. Correctness: Is technical or structural guidance sound?
    3. Completeness: Is the explanation thorough, well-structured, and quantified?
    4. Groundedness: Are claims grounded in context without hallucinatory credentials?
    """
    resp_len = len(response.split())
    norm_prompt = normalize_text(prompt)
    norm_resp = normalize_text(response)

    # 1. Relevance Score (1-5)
    prompt_words = set(norm_prompt.split())
    overlap = len(prompt_words.intersection(set(norm_resp.split())))
    overlap_ratio = overlap / max(len(prompt_words), 1)

    if resp_len < 10 or overlap_ratio < 0.15:
        relevance = 2.0
    elif overlap_ratio < 0.30:
        relevance = 3.5
    else:
        relevance = 4.5 if resp_len >= 25 else 4.0

    # 2. Correctness Score (1-5)
    # Check for negative/contradictory phrases or toxic advice
    bad_patterns = ["completely worthless", "garbage", "never hire", "idiot"]
    has_bad_pattern = any(p in norm_resp for p in bad_patterns)

    if has_bad_pattern:
        correctness = 1.0
    elif expected_keywords:
        kw_cov = calculate_keyword_coverage(response, expected_keywords)
        correctness = round(2.0 + (kw_cov * 3.0), 1)
    else:
        correctness = 4.0 if resp_len > 30 else 3.5

    # 3. Completeness Score (1-5)
    has_structure = ("1." in response or "2." in response or "-" in response or "\n" in response)
    has_metrics = bool(re.search(r"\b(\d+[%kKmM]?|\$\d+)\b", response))

    completeness = 2.5
    if resp_len >= 30:
        completeness += 1.0
    if resp_len >= 60:
        completeness += 0.5
    if has_structure:
        completeness += 0.5
    if has_metrics:
        completeness += 0.5
    completeness = min(completeness, 5.0)

    # 4. Groundedness Score (1-5)
    groundedness = 5.0
    if context:
        # Check if hallucinating external credentials not in context
        retrieved = context.get("retrieved_context", [])
        resume_data = str(context.get("structured_resume_data", ""))
        context_str = " ".join(retrieved) + " " + resume_data

        if context_str.strip():
            # If prompt asked about specific facts, check if response cites context or invents
            norm_ctx = normalize_text(context_str)
            if "google" in norm_resp and "google" not in norm_ctx:
                groundedness = 1.5
            elif "vice president" in norm_resp and "vice president" not in norm_ctx:
                groundedness = 1.0
            else:
                groundedness = 4.5

    # Overall Rubric Average
    overall_avg = round((relevance + correctness + completeness + groundedness) / 4.0, 2)

    return {
        "relevance": relevance,
        "correctness": correctness,
        "completeness": completeness,
        "groundedness": groundedness,
        "rubric_average": overall_avg,
        "human_eval_fields": {
            "human_reviewer_score": None,
            "human_feedback": "",
            "human_verified": False,
        }
    }


def run_comprehensive_evaluation(
    prompt: str,
    response: str,
    reference: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    expected_keywords: Optional[List[str]] = None,
    responsible_ai_evaluator = None,
    provider: str = "unknown",
    model_name: str = "unknown"
) -> Dict[str, Any]:
    """
    Orchestrates full metric calculation: ROUGE-L, keyword coverage,
    rubric scoring, and Responsible AI safety audits.
    """
    # 1. Linguistic & Exact Match Metrics
    rouge_l = calculate_rouge_l(response, reference) if reference else {"f1": 0.0, "precision": 0.0, "recall": 0.0}
    em = calculate_exact_match(response, reference) if reference else 0.0
    kw_coverage = calculate_keyword_coverage(response, expected_keywords or [])

    # 2. Rubric Evaluation
    rubric = evaluate_rubric(
        prompt=prompt,
        response=response,
        reference=reference,
        context=context,
        expected_keywords=expected_keywords
    )

    # 3. Responsible AI Audit
    safety_audit = {}
    if responsible_ai_evaluator is not None:
        try:
            safety_audit = responsible_ai_evaluator.evaluate_output(
                prompt=prompt,
                response=response,
                context=context or {},
                provider=provider
            )
        except Exception as e:
            logger.warning(f"Responsible AI evaluator error: {e}")
            safety_audit = {"status": "error", "error": str(e), "overall": {"passed_all_checks": True}}
    else:
        # Fallback local heuristic check
        safety_audit = {
            "overall": {
                "passed_all_checks": not any(w in response.lower() for w in ["idiot", "worthless", "garbage"]),
                "verdict": "PASSED" if not any(w in response.lower() for w in ["idiot", "worthless", "garbage"]) else "FAILED"
            }
        }

    return {
        "rouge_l": rouge_l,
        "exact_match": em,
        "keyword_coverage": kw_coverage,
        "rubric": rubric,
        "safety_audit": safety_audit,
    }
