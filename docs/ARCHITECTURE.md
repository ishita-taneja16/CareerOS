# 🏛️ CareerOS System Architecture

CareerOS is an enterprise-grade agentic AI career copilot designed with multi-agent orchestration, hybrid semantic retrieval, multi-provider model routing, production observability, and responsible AI guardrails.

---

## 1. High-Level System Architecture

```
                                    ┌────────────────────────┐
                                    │  React (Vite) Frontend │
                                    └───────────┬────────────┘
                                                │ REST / SSE
                                                ▼
                                    ┌────────────────────────┐
                                    │    FastAPI Gateway     │
                                    └───────────┬────────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 │                                                             │
                 ▼                                                             ▼
   ┌───────────────────────────┐                                 ┌───────────────────────────┐
   │    Document & ATS APIs    │                                 │   Agent Chat Orchestrator │
   │ (PyMuPDF, docling, spacy) │                                 │        (LangGraph)        │
   └─────────────┬─────────────┘                                 └─────────────┬─────────────┘
                 │                                                             │
                 ▼                                                             ▼
   ┌───────────────────────────┐                                 ┌───────────────────────────┐
   │ Hybrid RAG Vector Engine  │◄────────────────────────────────┤   Supervisor StateGraph   │
   │ (ChromaDB + BM25 + RRF)   │                                 │   (7 Specialist Agents)   │
   └───────────────────────────┘                                 └─────────────┬─────────────┘
                                                                               │
                                                                               ▼
                                                                 ┌───────────────────────────┐
                                                                 │      Central LLMService   │
                                                                 │  (Gemini, OpenAI, Qwen)   │
                                                                 └─────────────┬─────────────┘
                                                                               │
                                 ┌─────────────────────────────────────────────┴────────────────┐
                                 ▼                                                              ▼
                  ┌──────────────────────────────┐                              ┌──────────────────────────────┐
                  │    Responsible AI Engine     │                              │ Langfuse Tracing & Telemetry │
                  │ (Toxicity, Bias, Grounded)   │                              │ (Spans, Tokens, Latency)     │
                  └──────────────────────────────┘                              └──────────────────────────────┘
```

---

## 2. Multi-Agent Orchestration (LangGraph)

The core agent intelligence is powered by **LangGraph** using a **Supervisor-Worker Architecture**:

```
                              ┌──────────────┐
                              │  User Query  │
                              └──────┬───────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │    Supervisor Agent    │
                        │ (Routing Decision LLM) │
                        └────────────┬───────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │   Pipeline Dispatcher  │◄─────────────┐
                        └────────────┬───────────┘              │
                                     │                          │
                 ┌───────────────────┼───────────────────┐      │
                 ▼                   ▼                   ▼      │
         ┌───────────────┐   ┌───────────────┐   ┌──────────────┐
         │ Resume Agent  │   │   ATS Agent   │   │ Advisor Agent│
         └───────┬───────┘   └───────┬───────┘   └───────┬──────┘
                 │                   │                   │      │
                 └───────────────────┼───────────────────┘      │
                                     │                          │
                 ┌───────────────────┼───────────────────┐      │
                 ▼                   ▼                   ▼      │
         ┌───────────────┐   ┌───────────────┐   ┌──────────────┐
         │Interview Agent│   │Skill Gap Agent│   │Cover Letter  │
         └───────┬───────┘   └───────┬───────┘   └───────┬──────┘
                 │                   │                   │      │
                 └───────────────────┼───────────────────┘      │
                                     │                          │
                                     ▼                          │
                             ┌───────────────┐                  │
                             │ Memory Agent  │──────────────────┘
                             └───────┬───────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  END / Response │
                            └─────────────────┘
```

### Key Agents
1. **Supervisor (`agents/supervisor.py`)**: Evaluates conversation history and dynamically routes to the optimal specialist or schedules an execution pipeline (`routing_pipeline`).
2. **Pipeline Dispatcher (`agents/graph.py`)**: State router popping scheduled agents sequentially or terminating at `END`.
3. **Resume Agent (`agents/resume_agent.py`)**: Edits and rewrites structured resume JSON while preserving schema integrity.
4. **ATS Agent (`agents/ats_agent.py`)**: Computes keyword coverage, structural scores, and prioritized improvements.
5. **Advisor Agent (`agents/advisor_agent.py`)**: Generates strategic career coaching by blending resume context with retrieved user memories.
6. **Interview Agent (`agents/interview_agent.py`)**: Conducts technical and behavioral mock interview sessions using the STAR methodology.
7. **Skill Gap Agent (`agents/skill_gap_agent.py`)**: Compares resume skills against target job descriptions and generates targeted learning roadmaps.
8. **Cover Letter Agent (`agents/cover_letter_agent.py`)**: Synthesizes personalized, role-aligned cover letters.
9. **Memory Agent (`agents/memory_agent.py`)**: Extracts user preferences, skills, and goals from conversation turns and stores them in ChromaDB.

### Immutable State Machine (`AgentState`)
```python
class AgentState(BaseModel):
    user_id: str
    active_resume_version_id: Optional[str] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    job_description: Optional[str] = None
    routing_destination: str = "supervisor"
    routing_pipeline: List[str] = Field(default_factory=list)
    structured_resume_data: Optional[Dict[str, Any]] = None
    ats_results: Optional[Dict[str, Any]] = None
    interview_session_id: Optional[str] = None
    last_response: Optional[str] = None
```

---

## 3. RAG & Hybrid Retrieval Engine

CareerOS implements a **two-stage Hybrid Search with Reciprocal Rank Fusion (RRF)** in `services/vector_service.py`:

```
                       ┌─────────────────────────┐
                       │ User Query / Job Search │
                       └────────────┬────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
       ┌────────────────────────┐      ┌────────────────────────┐
       │ Dense Vector Search    │      │ Sparse Lexical Search  │
       │ (ChromaDB MiniLM)      │      │ (BM25Okapi Engine)     │
       └────────────┬───────────┘      └────────────┬───────────┘
                    │                               │
                    │ Dense Ranks                   │ Sparse Ranks
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  Reciprocal Rank Fusion (RRF) │
                    │   score = Σ [ w / (k + rank) ]│
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  Top-K Re-ranked Context      │
                    │  (Fed to Agent Prompt)        │
                    └───────────────────────────────┘
```

- **Dense Stage**: ChromaDB vector index captures latent semantic concepts (e.g. matching "distributed systems" with "microservices architecture").
- **Sparse Stage**: `BM25OkapiRetriever` captures exact technical acronyms, tools, and certifications (e.g. `FastAPI`, `PostgreSQL`, `QLoRA`, `Alembic`).
- **Fusion**: Standard RRF formula with constant $k=60$ merges both retrieval distributions, ensuring robust recall without score distribution calibration issues.

---

## 4. LLM Provider Routing & Resilience

`LLMService` (`services/llm_service.py`) provides unified routing across multiple providers:

- **Google Gemini** (`gemini/gemini-2.5-flash`): Primary production provider for low-latency reasoning and structured JSON output.
- **OpenAI** (`openai/gpt-4o-mini`, `gpt-4o`): High-throughput alternative with native structured outputs.
- **Qwen** (`huggingface/Qwen/Qwen2.5-7B-Instruct`, local vLLM/Ollama): Local privacy-focused and fine-tuned open-weights models.
- **Ollama / HuggingFace**: Self-hosted local instances.

### Resilience & Error Handling
- **Exponential Backoff**: Configurable retries (default 3) with exponential delay ($1.0s \to 2.0s \to 4.0s$).
- **ContextVar Retry Tracking**: `llm_retry_count_var` propagates real retry attempts across asynchronous graph executions.
- **Error Classification**: Specific log categorization for authentication failures, rate limit quotas (HTTP 429), and connection timeouts.

---

## 5. Agent Monitoring & Observability (Langfuse)

Observability is implemented in `core/tracer.py` and `core/logging_decorator.py`:

- **Agent Spans**: Every agent node (`@agent_logger`) automatically generates a span tracking duration, input state metadata, routing destination, and exceptions.
- **Generation Tracking**: Every LLM call records prompt, completion text, latency, provider, and exact token counts (`prompt_tokens`, `completion_tokens`, `total_tokens`).
- **Zero Fabrication**: Tokens and costs are only recorded when directly exposed by the provider/LiteLLM. Missing metrics are left as `None`.
- **Graceful Degradation**: If `LANGFUSE_ENABLED=false` or credentials are missing, the system operates seamlessly with `NoOpSpan`, adding zero latency and zero risk of failure.

---

## 6. Responsible AI Guardrails & Evaluation

Before LLM calls and before output delivery, inputs and outputs are validated via `ml/responsible_ai`:
1. **Input Guardrail**: Detects prompt injection patterns (`ignore previous instructions`, `bypass filter`).
2. **Toxicity Evaluator**: Scans for insults, profanity, and hostile recruiter/candidate language.
3. **Demographic Bias Detector**: Identifies gender/demographic bias in candidate recommendations.
4. **Factual Groundedness Auditor**: Validates generated claims against source resume JSON and retrieved RAG context.
