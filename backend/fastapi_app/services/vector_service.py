import os
# pyrefly: ignore [missing-import]
import chromadb
# pyrefly: ignore [missing-import]
from chromadb.config import Settings as ChromaSettings
# pyrefly: ignore [missing-import]
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from config import settings

class VectorStoreService:
    def __init__(self):
        # Fall back to local SQLite Chroma storage if not running in container or if connection fails
        self.client = None
        if settings.CHROMA_HOST == "chroma" and os.environ.get("RUNNING_IN_DOCKER"):
            try:
                self.client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT
                )
            except Exception:
                self.client = None

        if not self.client:
            # Running locally outside Docker
            persist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db_store")
            self.client = chromadb.PersistentClient(path=persist_dir)

        # Initialize Default Embedding Function
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        # Initialize Collections
        self.memories_col = self.client.get_or_create_collection(
            name="user_memories",
            embedding_function=self.embedding_fn
        )
        self.resumes_col = self.client.get_or_create_collection(
            name="resume_chunks",
            embedding_function=self.embedding_fn
        )

    # --- Memories Management ---
    def add_memory(self, user_id: str, text: str, category: str) -> None:
        """Stores a custom fact or preference in ChromaDB for long term recall."""
        import uuid
        memory_id = f"mem_{uuid.uuid4().hex}"
        self.memories_col.add(
            documents=[text],
            metadatas=[{
                "user_id": user_id,
                "category": category
            }],
            ids=[memory_id]
        )

    def query_memories(self, user_id: str, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves semantic memory contexts matching the search phrase."""
        results = self.memories_col.query(
            query_texts=[query_text],
            where={"user_id": user_id},
            n_results=limit
        )
        memories = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0]*len(docs)
            for doc, meta, dist in zip(docs, metas, distances):
                memories.append({
                    "text": doc,
                    "category": meta.get("category"),
                    "distance": dist
                })
        return memories

    # --- Resume Chunks Management ---
    def index_resume(self, user_id: str, resume_version_id: str, resume_data: Dict[str, Any]) -> None:
        """Splits and indexes resume segments (experiences, projects, etc) for RAG lookup."""
        # 1. Clean previous chunks for this version if any
        try:
            self.resumes_col.delete(where={"resume_version_id": resume_version_id})
        except Exception:
            pass

        documents = []
        metadatas = []
        ids = []
        chunk_count = 0

        # Chunk Skills
        skills = resume_data.get("skills", [])
        if skills:
            skills_txt = "Technical Skills: " + ", ".join(skills)
            documents.append(skills_txt)
            metadatas.append({
                "user_id": user_id,
                "resume_version_id": resume_version_id,
                "section": "skills"
            })
            ids.append(f"res_{resume_version_id}_skills")

        # Chunk Experiences
        experiences = resume_data.get("experiences", [])
        for i, exp in enumerate(experiences):
            role_desc = f"Professional Experience: {exp.get('role')} at {exp.get('company')} in {exp.get('location')}. "
            bullets = exp.get("description_bullets", [])
            for j, bullet in enumerate(bullets):
                chunk_txt = role_desc + bullet
                documents.append(chunk_txt)
                metadatas.append({
                    "user_id": user_id,
                    "resume_version_id": resume_version_id,
                    "section": "experience",
                    "item_index": i,
                    "bullet_index": j
                })
                ids.append(f"res_{resume_version_id}_exp_{i}_{j}")

        # Chunk Projects
        projects = resume_data.get("projects", [])
        for i, proj in enumerate(projects):
            proj_desc = f"Project Accomplishment: {proj.get('name')}. "
            bullets = proj.get("description_bullets", [])
            for j, bullet in enumerate(bullets):
                chunk_txt = proj_desc + bullet
                documents.append(chunk_txt)
                metadatas.append({
                    "user_id": user_id,
                    "resume_version_id": resume_version_id,
                    "section": "projects",
                    "item_index": i,
                    "bullet_index": j
                })
                ids.append(f"res_{resume_version_id}_proj_{i}_{j}")

        if documents:
            self.resumes_col.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def query_resume_chunks(
        self,
        user_id: str,
        resume_version_id: str,
        query_text: str,
        limit: int = 5,
        use_hybrid: bool = False,
    ) -> List[str]:
        """
        Queries resume RAG context relevant to a job search or user query.
        When use_hybrid is True, leverages dense + BM25 reciprocal rank fusion reranking.
        """
        if use_hybrid:
            hybrid_results = self.query_resume_chunks_hybrid(
                user_id=user_id,
                resume_version_id=resume_version_id,
                query_text=query_text,
                limit=limit
            )
            return [res["text"] for res in hybrid_results]

        results = self.resumes_col.query(
            query_texts=[query_text],
            where={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"resume_version_id": {"$eq": resume_version_id}}
                ]
            },
            n_results=limit
        )
        if results and results["documents"]:
            return results["documents"][0]
        return []

    def query_resume_chunks_hybrid(
        self,
        user_id: str,
        resume_version_id: str,
        query_text: str,
        limit: int = 5,
        alpha: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining ChromaDB dense vector embeddings with BM25 sparse keyword ranking,
        reranked using Reciprocal Rank Fusion (RRF) and query term overlap.
        Returns ranked list of candidate chunks with scores and metadata.
        """
        where_filter = {
            "$and": [
                {"user_id": {"$eq": user_id}},
                {"resume_version_id": {"$eq": resume_version_id}}
            ]
        }

        # 1. Fetch candidate pool via Dense Vector Query
        dense_results = self.resumes_col.query(
            query_texts=[query_text],
            where=where_filter,
            n_results=max(limit * 2, 10)
        )

        dense_ranked_ids: List[str] = []
        dense_docs_map: Dict[str, Dict[str, Any]] = {}

        if dense_results and dense_results.get("ids") and dense_results["ids"][0]:
            ids = dense_results["ids"][0]
            docs = dense_results["documents"][0]
            metas = dense_results["metadatas"][0] if dense_results.get("metadatas") else [{}] * len(ids)
            distances = dense_results["distances"][0] if dense_results.get("distances") else [0.0] * len(ids)

            for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
                dense_ranked_ids.append(doc_id)
                dense_docs_map[doc_id] = {
                    "id": doc_id,
                    "text": doc,
                    "metadata": meta,
                    "dense_distance": dist
                }

        # 2. Fetch all chunks for this resume to run sparse BM25 retrieval
        all_chunks = self.resumes_col.get(where=where_filter)
        all_ids = all_chunks.get("ids", [])
        all_docs = all_chunks.get("documents", [])
        all_metas = all_chunks.get("metadatas", []) or [{}] * len(all_ids)

        if not all_docs:
            return []

        # Populate docs map with any chunks not in dense pool
        for doc_id, doc, meta in zip(all_ids, all_docs, all_metas):
            if doc_id not in dense_docs_map:
                dense_docs_map[doc_id] = {
                    "id": doc_id,
                    "text": doc,
                    "metadata": meta,
                    "dense_distance": 1.0
                }

        # 3. BM25 Sparse Keyword Scoring
        bm25 = BM25OkapiRetriever(corpus=all_docs, doc_ids=all_ids)
        sparse_scores = bm25.score_query(query_text)
        sparse_ranked_ids = [doc_id for doc_id, score in sorted(sparse_scores.items(), key=lambda x: x[1], reverse=True)]

        # 4. Reciprocal Rank Fusion (RRF) Reranking
        k = 60
        rrf_scores: Dict[str, float] = {}

        # Dense RRF contribution
        for rank, doc_id in enumerate(dense_ranked_ids, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 - alpha) * (1.0 / (k + rank))

        # Sparse RRF contribution
        for rank, doc_id in enumerate(sparse_ranked_ids, start=1):
            if sparse_scores.get(doc_id, 0.0) > 0:
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + alpha * (1.0 / (k + rank))

        # 5. Build reranked output
        ranked_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        final_results = []
        for doc_id, score in ranked_candidates[:limit]:
            item = dense_docs_map.get(doc_id, {})
            final_results.append({
                "id": doc_id,
                "text": item.get("text", ""),
                "metadata": item.get("metadata", {}),
                "hybrid_score": round(score, 6),
                "bm25_score": round(sparse_scores.get(doc_id, 0.0), 4),
            })

        return final_results

    def query_memories_hybrid(self, user_id: str, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Hybrid memory retrieval using dense vector similarity plus BM25 keyword scoring."""
        all_memories = self.memories_col.get(where={"user_id": user_id})
        ids = all_memories.get("ids", [])
        docs = all_memories.get("documents", [])
        metas = all_memories.get("metadatas", []) or [{}] * len(ids)

        if not docs:
            return []

        # Dense query
        dense_res = self.memories_col.query(query_texts=[query_text], where={"user_id": user_id}, n_results=min(limit * 2, len(docs)))
        dense_ids = dense_res.get("ids", [[]])[0] if dense_res else []

        # Sparse query
        bm25 = BM25OkapiRetriever(corpus=docs, doc_ids=ids)
        sparse_scores = bm25.score_query(query_text)
        sparse_ids = [doc_id for doc_id, _ in sorted(sparse_scores.items(), key=lambda x: x[1], reverse=True)]

        # RRF Rerank
        k = 60
        rrf: Dict[str, float] = {}
        for r, doc_id in enumerate(dense_ids, start=1):
            rrf[doc_id] = rrf.get(doc_id, 0.0) + 0.5 * (1.0 / (k + r))
        for r, doc_id in enumerate(sparse_ids, start=1):
            if sparse_scores.get(doc_id, 0.0) > 0:
                rrf[doc_id] = rrf.get(doc_id, 0.0) + 0.5 * (1.0 / (k + r))

        docs_map = {doc_id: (doc, meta) for doc_id, doc, meta in zip(ids, docs, metas)}
        ranked = sorted(rrf.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in ranked[:limit]:
            doc, meta = docs_map.get(doc_id, ("", {}))
            results.append({
                "text": doc,
                "category": meta.get("category"),
                "hybrid_score": round(score, 6)
            })
        return results


class BM25OkapiRetriever:
    """
    BM25Okapi sparse retrieval engine for hybrid search.
    Utilizes rank_bm25 when installed, with seamless fallback to pure-python Okapi BM25 scoring.
    """
    def __init__(self, corpus: List[str], doc_ids: Optional[List[str]] = None, k1: float = 1.5, b: float = 0.75):
        import math
        import re

        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_ids = doc_ids or [str(i) for i in range(self.corpus_size)]
        self.tokenized_corpus = [[w.lower() for w in re.findall(r"\w+", doc)] for doc in corpus]

        self._bm25_instance = None
        try:
            from rank_bm25 import BM25Okapi
            if self.corpus_size > 0:
                self._bm25_instance = BM25Okapi(self.tokenized_corpus, k1=k1, b=b)
        except ImportError:
            self._bm25_instance = None

        # Precompute fallback metadata for environments without rank_bm25
        if self._bm25_instance is None:
            self.doc_lens = [len(tokens) for tokens in self.tokenized_corpus]
            self.doc_freqs: Dict[str, int] = {}
            for tokens in self.tokenized_corpus:
                seen = set(tokens)
                for token in seen:
                    self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

            self.avg_doc_len = (sum(self.doc_lens) / self.corpus_size) if self.corpus_size > 0 else 1.0

            # Precompute IDF (Robertson-Spärck Jones formula)
            self.idf: Dict[str, float] = {}
            for token, freq in self.doc_freqs.items():
                self.idf[token] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def score_query(self, query: str) -> Dict[str, float]:
        import re
        query_tokens = [w.lower() for w in re.findall(r"\w+", query)]
        scores: Dict[str, float] = {}

        if self.corpus_size == 0 or not query_tokens:
            return {doc_id: 0.0 for doc_id in self.doc_ids}

        # Use rank_bm25 if available
        if self._bm25_instance is not None:
            raw_scores = self._bm25_instance.get_scores(query_tokens)
            for doc_id, score in zip(self.doc_ids, raw_scores):
                scores[doc_id] = float(max(score, 0.0))
            return scores

        # Fallback pure-python BM25 computation
        for doc_idx, (doc_id, tokens, doc_len) in enumerate(zip(self.doc_ids, self.tokenized_corpus, self.doc_lens)):
            score = 0.0
            if doc_len == 0:
                scores[doc_id] = 0.0
                continue

            token_counts: Dict[str, int] = {}
            for t in tokens:
                token_counts[t] = token_counts.get(t, 0) + 1

            for q in query_tokens:
                if q in token_counts:
                    tf = token_counts[q]
                    idf = self.idf.get(q, 0.0)
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                    score += idf * (numerator / denominator)

            scores[doc_id] = max(score, 0.0)

        return scores
