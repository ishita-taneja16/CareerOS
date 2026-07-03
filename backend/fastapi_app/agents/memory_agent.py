from agents.state import AgentState
from services.llm_service import LLMService
from services.vector_service import VectorStoreService
from core.logging_decorator import agent_logger
from prompts.memory_prompt import MEMORY_EXTRACTION_PROMPT

vector_store = VectorStoreService()

@agent_logger("memory_agent")
def run_memory_agent(state: AgentState) -> dict:
    """
    MemoryAgent. Retreives relevant memories from vector database to append to context,
    and analyzes user messages to save new skills, goals, projects, or preferences.
    """
    user_id = state.get("user_id") if isinstance(state, dict) else getattr(state, "user_id", "unknown")
    messages = state.get("messages", []) if isinstance(state, dict) else getattr(state, "messages", [])
    latest_user_message = messages[-1]["content"] if messages else ""

    # 1. Retrieve memories relevant to user query
    retrieved = []
    if latest_user_message:
        memories = vector_store.query_memories(user_id, latest_user_message, limit=3)
        retrieved = [f"- {m['category'].capitalize()}: {m['text']}" for m in memories]
    
    memory_context = "\n".join(retrieved) if retrieved else "No previous preferences recorded."

    # 2. Analyze user message to extract and save new facts/preferences
    if latest_user_message:
        prompt = MEMORY_EXTRACTION_PROMPT.format(message=latest_user_message)
        try:
            extracted_fact = LLMService.call(prompt=prompt).strip()
            if extracted_fact and len(extracted_fact) > 5 and not extracted_fact.lower().startswith("no"):
                category = "preference"
                lower_msg = latest_user_message.lower()
                if "skill" in lower_msg or "learn" in lower_msg:
                    category = "skill"
                elif "experience" in lower_msg or "worked" in lower_msg:
                    category = "experience"
                elif "goal" in lower_msg or "career" in lower_msg:
                    category = "goal"
                elif "project" in lower_msg:
                    category = "project"
                
                vector_store.add_memory(user_id, extracted_fact, category)
        except Exception:
            pass

    # 3. Check if there is interview feedback in the state that needs to be stored
    ats_results = state.get("ats_results") if isinstance(state, dict) else getattr(state, "ats_results", None)
    if ats_results and isinstance(ats_results, dict):
        suggestions = ats_results.get("priority_suggestions", [])
        if suggestions:
            vector_store.add_memory(user_id, f"Needs to work on: {', '.join(suggestions[:3])}", "improvement")

    # We store the memory context inside last_response or return it so other nodes can use it
    # We will pass the retrieved context to the state context
    return {
        "last_response": f"System recalled context: {memory_context[:100]}...",
        "routing_destination": "pipeline_dispatcher"
    }
