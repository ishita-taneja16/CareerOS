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

    def query_resume_chunks(self, user_id: str, resume_version_id: str, query_text: str, limit: int = 5) -> List[str]:
        """Queries resume RAG context relevant to a job search or user query."""
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
