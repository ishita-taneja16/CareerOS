"""
Unit Tests for CareerOS Evaluation Metrics & Scoring Engine
"""

import pytest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.evaluation.metrics import (
    normalize_text,
    calculate_rouge_l,
    calculate_exact_match,
    calculate_keyword_coverage,
    evaluate_rubric,
    run_comprehensive_evaluation,
)


def test_text_normalization():
    raw = "  Hello, World! This is a TEST...  "
    norm = normalize_text(raw)
    assert norm == "hello world this is a test"


def test_calculate_rouge_l_identical_text():
    text = "Engineered asynchronous FastAPI microservices with Redis caching"
    scores = calculate_rouge_l(text, text)
    assert scores["precision"] == 1.0
    assert scores["recall"] == 1.0
    assert scores["f1"] == 1.0


def test_calculate_rouge_l_disjoint_text():
    cand = "Completely different content about cooking food"
    ref = "PostgreSQL database query optimization techniques"
    scores = calculate_rouge_l(cand, ref)
    assert scores["f1"] == 0.0


def test_calculate_rouge_l_partial_overlap():
    cand = "FastAPI backend services with Redis"
    ref = "FastAPI asynchronous microservices with Redis caching and Docker"
    scores = calculate_rouge_l(cand, ref)
    assert scores["precision"] > 0.0
    assert scores["recall"] > 0.0
    assert scores["f1"] > 0.0
    assert scores["precision"] <= 1.0


def test_calculate_exact_match():
    assert calculate_exact_match("Python Developer", "python developer!") == 1.0
    assert calculate_exact_match("FastAPI", "Django") == 0.0


def test_calculate_keyword_coverage():
    text = "Experienced in FastAPI, PostgreSQL, Docker, and Pytest."
    keywords = ["FastAPI", "PostgreSQL", "Docker", "Kubernetes"]
    cov = calculate_keyword_coverage(text, keywords)
    # 3 out of 4 matched = 0.75
    assert cov == 0.75

    # Empty keywords returns 1.0
    assert calculate_keyword_coverage(text, []) == 1.0


def test_evaluate_rubric_structure_and_scores():
    prompt = "How do I optimize a resume for an ATS scanner?"
    response = (
        "Here are 3 key steps to optimize your resume for ATS:\n"
        "1. Incorporate exact technical keywords from the job description.\n"
        "2. Use clean standard formatting without graphic elements or columns.\n"
        "3. Quantify impact with metrics, e.g. improved throughput by 35%."
    )
    rubric = evaluate_rubric(prompt, response, expected_keywords=["keywords", "formatting"])

    assert 1.0 <= rubric["relevance"] <= 5.0
    assert 1.0 <= rubric["correctness"] <= 5.0
    assert 1.0 <= rubric["completeness"] <= 5.0
    assert 1.0 <= rubric["groundedness"] <= 5.0
    assert 1.0 <= rubric["rubric_average"] <= 5.0
    assert "human_eval_fields" in rubric
    assert rubric["human_eval_fields"]["human_verified"] is False


def test_rubric_penalizes_toxic_or_destructive_advice():
    prompt = "How should I handle a bad candidate?"
    toxic_response = "Candidate is an absolute idiot, completely worthless, useless, and garbage."
    rubric = evaluate_rubric(prompt, toxic_response)
    assert rubric["correctness"] == 1.0


def test_rubric_detects_hallucinated_credentials():
    prompt = "Where did the candidate work?"
    hallucinated = "You worked at Google for 15 years as Vice President of Engineering."
    context = {
        "retrieved_context": ["Junior developer at local marketing agency (2022-2024)."]
    }
    rubric = evaluate_rubric(prompt, hallucinated, context=context)
    assert rubric["groundedness"] <= 1.5


def test_comprehensive_evaluation_pipeline():
    prompt = "What backend framework should I learn for modern Python APIs?"
    response = "Learn FastAPI because it offers native asynchronous I/O, Pydantic v2 validation, and OpenAPI documentation."
    ref = "FastAPI is the recommended modern Python framework for high-performance async APIs."

    results = run_comprehensive_evaluation(
        prompt=prompt,
        response=response,
        reference=ref,
        expected_keywords=["FastAPI", "Pydantic"],
        provider="test_provider",
        model_name="TestModel"
    )

    assert "rouge_l" in results
    assert "exact_match" in results
    assert "keyword_coverage" in results
    assert "rubric" in results
    assert "safety_audit" in results
    assert results["safety_audit"]["overall"]["passed_all_checks"] is True
