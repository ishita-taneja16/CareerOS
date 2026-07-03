import json
from agents.state import AgentState
from services.llm_service import LLMService
from core.logging_decorator import agent_logger
from prompts.resume_prompt import RESUME_MODIFICATION_PROMPT

@agent_logger("resume_agent")
def run_resume_agent(state: AgentState) -> dict:
    """
    ResumeAgent. Modifies structure of active resume JSON data and writes descriptions.
    """
    messages = state.get("messages", []) if isinstance(state, dict) else getattr(state, "messages", [])
    latest_user_message = messages[-1]["content"] if messages else ""
    
    resume_json = state.get("structured_resume_data", {}) if isinstance(state, dict) else getattr(state, "structured_resume_data", {})
    if not resume_json:
        resume_json = {}
        
    prompt = RESUME_MODIFICATION_PROMPT.format(
        user_instruction=latest_user_message,
        resume_json=json.dumps(resume_json, indent=2)
    )

    try:
        content = LLMService.call(
            prompt=prompt,
            response_format={"type": "json_object"}
        )
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        modified_resume = json.loads(content)
        return {
            "structured_resume_data": modified_resume,
            "last_response": "I've successfully updated your resume data. You can view the modified version in the editor pane.",
            "routing_destination": "pipeline_dispatcher"
        }
    except Exception as e:
        return {
            "last_response": f"Failed to modify the resume: {str(e)}",
            "routing_destination": "pipeline_dispatcher"
        }
