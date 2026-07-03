from agents.state import AgentState
from services.llm_service import LLMService
from core.logging_decorator import agent_logger
from prompts.skill_gap_prompt import SKILL_GAP_PROMPT

@agent_logger("skill_gap_agent")
def run_skill_gap_agent(state: AgentState) -> dict:
    """
    SkillGapAgent. Identifies missing skill roadmaps and estimates prep time.
    """
    resume_json = state.get("structured_resume_data") if isinstance(state, dict) else getattr(state, "structured_resume_data", {})
    if not resume_json or not state.get("job_description"):
        return {
            "last_response": "I need your resume details and the target Job Description to run a Skill Gap Analysis.",
            "routing_destination": "pipeline_dispatcher"
        }

    resume_skills = resume_json.get("skills", [])
    jd = state.get("job_description") if isinstance(state, dict) else getattr(state, "job_description", "")

    prompt = SKILL_GAP_PROMPT.format(
        skills_list=", ".join(resume_skills),
        jd_text=jd
    )

    try:
        roadmap = LLMService.call(prompt=prompt)
        return {
            "last_response": roadmap.strip(),
            "routing_destination": "pipeline_dispatcher"
        }
    except Exception as e:
        return {
            "last_response": f"Failed to perform skill gap analysis: {str(e)}",
            "routing_destination": "pipeline_dispatcher"
        }
