import json
from agents.state import AgentState
from services.llm_service import LLMService
from core.logging_decorator import agent_logger
from prompts.interview_prompt import INTERVIEW_AGENT_PROMPT

@agent_logger("interview_agent")
def run_interview_agent(state: AgentState) -> dict:
    """
    InterviewAgent. Conducts simulated HR/Technical mock recruiter interviews.
    """
    messages = state.get("messages", []) if isinstance(state, dict) else getattr(state, "messages", [])
    latest_user_message = messages[-1]["content"] if messages else ""
    
    jd = state.get("job_description") if isinstance(state, dict) else getattr(state, "job_description", "Software Engineering Generalist Role")
    resume_json = state.get("structured_resume_data") if isinstance(state, dict) else getattr(state, "structured_resume_data", {})
    
    history = [m for m in messages if m.get("role") != "system"]
    
    prompt = INTERVIEW_AGENT_PROMPT.format(
        jd_text=jd,
        resume_json=json.dumps(resume_json, indent=2),
        history_str=json.dumps(history[-8:], indent=2),
        latest_user_message=latest_user_message
    )

    try:
        recruiter_reply = LLMService.call(prompt=prompt)
        return {
            "last_response": recruiter_reply.strip(),
            "routing_destination": "pipeline_dispatcher"
        }
    except Exception as e:
        return {
            "last_response": f"Interview simulator encountered an error: {str(e)}",
            "routing_destination": "pipeline_dispatcher"
        }
