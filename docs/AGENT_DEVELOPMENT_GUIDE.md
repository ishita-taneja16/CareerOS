# 📘 CareerOS Agent Development Guide

A comprehensive engineering guide for authoring, configuring, tracing, and testing multi-agent workflows in CareerOS.

---

## 1. Agent Design Principles

Every agent in CareerOS adheres to five foundational standards:
1. **Single Responsibility**: Each agent performs one specialized task (e.g. resume formatting, ATS scoring, career advisory).
2. **Explicit Typed State**: Nodes accept and return subsets of the typed `AgentState` Pydantic model.
3. **Structured Outputs**: Agents communicate using strictly validated JSON schemas with zero free-form ambiguity.
4. **End-to-End Tracing**: Every execution node is decorated with `@agent_logger`, emitting spans to Langfuse and structured logs.
5. **Responsible AI by Default**: All generation paths pass through input prompt injection guards and output factuality/bias audits.

---

## 2. Authoring a New Agent Node

### Step 1: Define the Specialist Function
Create your agent in `backend/fastapi_app/agents/<agent_name>_agent.py`:

```python
import json
from agents.state import AgentState
from services.llm_service import LLMService
from core.logging_decorator import agent_logger

MY_AGENT_PROMPT = """
You are the Specialized Career Coach.
Analyze the candidate's inquiry and provide high-impact, actionable guidance.

Inquiry: {user_instruction}
"""

@agent_logger("my_specialist_agent")
def run_my_specialist_agent(state: AgentState) -> dict:
    """Specialist node implementation."""
    messages = state.get("messages", []) if isinstance(state, dict) else getattr(state, "messages", [])
    latest_message = messages[-1]["content"] if messages else ""

    prompt = MY_AGENT_PROMPT.format(user_instruction=latest_message)

    try:
        response_text = LLMService.call(
            prompt=prompt,
            system_prompt="You are an expert career copilot specialist."
        )
        return {
            "last_response": response_text.strip(),
            "routing_destination": "pipeline_dispatcher"
        }
    except Exception as e:
        return {
            "last_response": f"Specialist encountered an error: {str(e)}",
            "routing_destination": "pipeline_dispatcher"
        }
```

### Step 2: Register Node in LangGraph
In `backend/fastapi_app/agents/graph.py`:

```python
from agents.my_specialist_agent import run_my_specialist_agent

def create_graph():
    workflow = StateGraph(AgentState)
    ...
    # 1. Register Node
    workflow.add_node("my_specialist_agent", run_my_specialist_agent)

    # 2. Add routing edge back to dispatcher
    workflow.add_edge("my_specialist_agent", "pipeline_dispatcher")
```

### Step 3: Update Supervisor Prompts
In `backend/fastapi_app/agents/supervisor.py`, add the new agent to the prompt list and `SupervisorDecision` model field description so the supervisor can intelligently route conversations to it.

---

## 3. Tool Schemas & Invocations

### Direct Service Tools (LangGraph)
In LangGraph, agents invoke services directly as deterministic Python functions:
```python
from services.vector_service import VectorStoreService
from services.ats_service import ATSEngine

vector_store = VectorStoreService()
ats_engine = ATSEngine()

# Dense + BM25 Hybrid Context Retrieval
contexts = vector_store.query_resume_chunks_hybrid(
    user_id=user_id,
    resume_version_id=version_id,
    query_text=query,
    limit=3
)
```

### Schema-Decorated Tools (CrewAI Prototype)
In the CrewAI prototype (`agents/crewai_demo/tools.py`), tools use the `@tool` decorator:
```python
from crewai.tools import tool

@tool("Tool Name")
def my_tool(param1: str, param2: int) -> str:
    """Docstring explaining tool purpose and parameters to the LLM."""
    return f"Processed {param1}"
```

---

## 4. State Management & Retries

### `AgentState` Schema
All state across the multi-agent graph flows through `agents/state.py`:
- `user_id`: Unique identifier for the user session.
- `messages`: Chronological list of chat message dictionaries.
- `structured_resume_data`: Validated JSON resume representation.
- `routing_destination`: Immediate next agent or `"end"`.
- `routing_pipeline`: Scheduled list of agents to run in sequence.

### Retries & Exponential Backoff
- `LLMService.call(retries=3, timeout=30)` executes exponential backoff (`delay *= 2`).
- Contextual retries are tracked using `llm_retry_count_var` (thread-safe ContextVar).

---

## 5. Observability & Langfuse Tracing

### Configuring Credentials
Configure environment variables in `.env`:
```bash
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_HOST="https://cloud.langfuse.com"
```

### Tracing Spans & Generations
- When `@agent_logger("agent_name")` executes, `tracer.trace_agent_execution` creates a span with user ID, execution duration, and routing metadata.
- When `LLMService.call` completes, `tracer.record_llm_generation` records prompt, completion, latency, and exact token counts (`prompt_tokens`, `completion_tokens`).
- Token usage and costs are never fabricated; if a provider does not expose token counts, the field is left empty.
- When `LANGFUSE_ENABLED=false`, the tracer degrades to `NoOpSpan` with zero performance overhead.

---

## 6. Responsible AI & Safety

All inputs and outputs pass through `ml/responsible_ai`:
1. **Input Guardrails**: Prevents prompt injection and system override attempts.
2. **Output Guardrails**: Audits toxic language, demographic bias, and ungrounded hallucinations.
3. Configure thresholds in `.env`:
   ```bash
   ENABLE_RESPONSIBLE_AI_GUARDRAILS=true
   BIAS_THRESHOLD=0.15
   MAX_HALLUCINATION_SCORE=0.20
   ```

---

## 7. Testing Best Practices

1. **Unit Testing Nodes with Mocks**:
   Always mock `LLMService.call` or underlying vector storage to avoid paid API calls and ensure instant test execution:
   ```python
   from unittest.mock import patch

   def test_my_agent():
       with patch("services.llm_service.LLMService.call", return_value="Mocked advice"):
           state = {"user_id": "test_1", "messages": [{"role": "user", "content": "Help me"}]}
           output = run_my_specialist_agent(state)
           assert "Mocked advice" in output["last_response"]
   ```

2. **Running Tests**:
   ```bash
   # Run all fast tests
   pytest backend/fastapi_app/tests/test_langfuse_tracing.py
   pytest backend/fastapi_app/tests/test_rag_optimization.py
   pytest backend/fastapi_app/tests/test_openai_provider.py
   pytest backend/fastapi_app/tests/test_responsible_ai.py
   pytest backend/fastapi_app/tests/test_crewai_demo.py
   ```
