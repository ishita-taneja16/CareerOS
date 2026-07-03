import json
from agents.state import AgentState
from services.llm_service import LLMService
from services.vector_service import VectorStoreService
from core.logging_decorator import agent_logger
from prompts.advisor_prompt import ADVISOR_AGENT_PROMPT

vector_store = VectorStoreService()

@agent_logger("advisor_agent")
def run_advisor_agent(state: AgentState) -> dict:
    """
    CareerAdvisorAgent. Handles general advice and career planning strategy.
    """
    messages = state.get("messages", []) if isinstance(state, dict) else getattr(state, "messages", [])
    latest_user_message = messages[-1]["content"] if messages else ""
    user_id = state.get("user_id") if isinstance(state, dict) else getattr(state, "user_id", "unknown")

    # 1. Fetch relevant user memories
    memories = vector_store.query_memories(user_id, latest_user_message, limit=3)
    memory_context = "\n".join([f"- Preference ({m['category']}): {m['text']}" for m in memories])

    # 2. Get active resume details
    resume_json = state.get("structured_resume_data") if isinstance(state, dict) else getattr(state, "structured_resume_data", None)
    resume_summary = json.dumps(resume_json, indent=2) if resume_json else "No active resume details uploaded yet."

    prompt = ADVISOR_AGENT_PROMPT.format(
        resume_summary=resume_summary,
        memory_context=memory_context if memory_context else "None recorded yet.",
        latest_user_message=latest_user_message
    )

    try:
        advisor_reply = LLMService.call(prompt=prompt)
        return {
            "last_response": advisor_reply.strip(),
            "routing_destination": "pipeline_dispatcher"
        }
    except Exception as e:
        return {
            "last_response": f"Career advisor encountered an error: {str(e)}",
            "routing_destination": "pipeline_dispatcher"
        }
