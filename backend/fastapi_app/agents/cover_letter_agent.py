import json
from agents.state import AgentState
from services.llm_service import LLMService
from core.logging_decorator import agent_logger
from prompts.cover_letter_prompt import COVER_LETTER_PROMPT

@agent_logger("cover_letter_agent")
def run_cover_letter_agent(state: AgentState) -> dict:
    """
    CoverLetterAgent. Drafts targeted cover letters.
    """
    resume_json = state.get("structured_resume_data") if isinstance(state, dict) else getattr(state, "structured_resume_data", None)
    if not resume_json:
        return {
            "last_response": "I need your resume details to draft a cover letter. Please upload a resume first.",
            "routing_destination": "pipeline_dispatcher"
        }

    jd = state.get("job_description") if isinstance(state, dict) else getattr(state, "job_description", "General software engineering role.")

    prompt = COVER_LETTER_PROMPT.format(
        jd_text=jd,
        resume_json=json.dumps(resume_json, indent=2)
    )

    try:
        cover_letter = LLMService.call(prompt=prompt)
        return {
            "last_response": cover_letter.strip(),
            "routing_destination": "pipeline_dispatcher"
        }
    except Exception as e:
        return {
            "last_response": f"Failed to generate cover letter: {str(e)}",
            "routing_destination": "pipeline_dispatcher"
        }
