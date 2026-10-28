import os
import sys
import pytest

# Align python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.vector_service import VectorStoreService, BM25OkapiRetriever
from ml.evaluation.eval_ragas import (
    compute_context_recall,
    compute_faithfulness,
    compute_reciprocal_rank,
    run_rag_evaluation,
)


def test_bm25_retriever_scoring():
    """Verify BM25 retrieval correctly scores exact keyword matches higher."""
    corpus = [
        "Specialized in FastAPI, asyncpg, PostgreSQL, and Redis caching.",
        "Experienced React and TypeScript frontend UI developer with Tailwind CSS.",
        "Machine learning researcher working on PyTorch, Transformers, and Qwen LoRA fine-tuning."
    ]
    doc_ids = ["doc_backend", "doc_frontend", "doc_ml"]

    retriever = BM25OkapiRetriever(corpus=corpus, doc_ids=doc_ids)

    # Query matching backend terms
    scores_backend = retriever.score_query("FastAPI PostgreSQL Redis")
    assert scores_backend["doc_backend"] > scores_backend["doc_frontend"]
    assert scores_backend["doc_backend"] > scores_backend["doc_ml"]

    # Query matching ML terms
    scores_ml = retriever.score_query("PyTorch Qwen fine-tuning")
    assert scores_ml["doc_ml"] > scores_ml["doc_backend"]
    assert scores_ml["doc_ml"] > scores_ml["doc_frontend"]


def test_vector_service_hybrid_query():
    """Verify that query_resume_chunks_hybrid returns ranked chunks with hybrid scores."""
    vector_store = VectorStoreService()
    user_id = "test_user_rag"
    resume_version_id = "v_test_rag"

    resume_data = {
        "skills": ["FastAPI", "PostgreSQL", "Docker"],
        "experiences": [
            {
                "company": "Tech Labs",
                "role": "Backend Engineer",
                "location": "Remote",
                "description_bullets": [
                    "Engineered asynchronous microservices using FastAPI and asyncpg.",
                    "Configured PostgreSQL database schemas and connection pooling."
                ]
            }
        ],
        "projects": [
            {
                "name": "Cloud Observability",
                "description_bullets": [
                    "Integrated Langfuse telemetry for real-time latency tracking."
                ]
            }
        ]
    }

    vector_store.index_resume(user_id=user_id, resume_version_id=resume_version_id, resume_data=resume_data)

    # Test hybrid query
    results = vector_store.query_resume_chunks_hybrid(
        user_id=user_id,
        resume_version_id=resume_version_id,
        query_text="FastAPI asyncpg microservices",
        limit=2
    )

    assert len(results) > 0
    assert "text" in results[0]
    assert "hybrid_score" in results[0]
    assert "FastAPI" in results[0]["text"] or "microservices" in results[0]["text"]

    # Test standard backward-compatible signature with use_hybrid=True
    chunks = vector_store.query_resume_chunks(
        user_id=user_id,
        resume_version_id=resume_version_id,
        query_text="Langfuse telemetry",
        limit=2,
        use_hybrid=True
    )
    assert isinstance(chunks, list)
    assert len(chunks) > 0


def test_ragas_evaluation_metrics():
    """Verify metric computation functions (context recall, faithfulness, and reciprocal rank)."""
    retrieved = [
        "Professional Experience: Senior AI Engineer. Built FastAPI endpoints with Redis caching.",
        "Technical Skills: Python, FastAPI, PostgreSQL, Redis, Docker."
    ]

    # Context recall test
    recall = compute_context_recall(
        retrieved_chunks=retrieved,
        target_skills=["FastAPI", "Redis", "Docker", "PostgreSQL"],
        ground_truth="Built FastAPI endpoints with Redis caching."
    )
    assert recall == 1.0

    # Partial recall test
    partial_recall = compute_context_recall(
        retrieved_chunks=retrieved,
        target_skills=["FastAPI", "Kubernetes", "AWS", "GCP"],
        ground_truth=""
    )
    assert partial_recall == 0.25

    # Faithfulness test - fully supported answer
    supported_answer = "The candidate built FastAPI endpoints with Redis caching."
    faith = compute_faithfulness(supported_answer, retrieved)
    assert faith == 1.0

    # Reciprocal rank test
    rr = compute_reciprocal_rank(retrieved, ["FastAPI"])
    assert rr == 1.0  # Found at rank 1
