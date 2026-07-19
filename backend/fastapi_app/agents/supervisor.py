from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from litellm import completion
from config import settings
from agents.state import AgentState

class SupervisorDecision(BaseModel):
    next_agent: str = Field(
        description="The next agent to route the conversation to: resume_agent, ats_agent, interview_agent, cover_letter_agent, skill_gap_agent, advisor_agent, or end"
    )
    reason: str = Field(description="Short rationale explaining the routing decision")

def run_supervisor(state: AgentState) -> dict:
    """
    Supervisor Node. Examines the conversation context and chooses the next worker node.
    """
    # 1. Format conversation history for supervisor
    history = []
    for msg in state.messages[-5:]: # Keep focus on last few turns
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history.append(f"{role.capitalize()}: {content}")
    history_str = "\n".join(history)

    prompt = f"""
You are the Supervisor Agent for an AI Career Copilot system.
Your job is to read the conversation history and route the user's latest request to the appropriate specialist agent.

Agents:
- `resume_agent`: Edits structured resume data, removes/adds skills/projects/experiences, rewrites bullet points, handles versioning.
- `ats_agent`: Audits ATS compatibility, keyword matches, formatting warnings, and analyzes resume constraints.
- `interview_agent`: Handles simulated HR/Technical recruiter mock runs and scores replies.
- `cover_letter_agent`: Writes personalized cover letters tailored to resumes and job requirements.
- `skill_gap_agent`: Analyzes skills missing from a job description, builds roadmap, recommends projects.
- `advisor_agent`: Handles general career goals, advice, job search preferences, and broad career questions.
- `end`: Choose this when the user is simply closing the conversation, greeting, or the last specialist agent has fully satisfied the query and no more specialist work is needed.

Conversation History:
{history_str}

Analyze the user's last message carefully. Output ONLY valid JSON matching the schema.
"""

    model = "gemini/gemini-2.5-flash" if settings.GEMINI_API_KEY else "ollama/llama3"
    api_key = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY else None

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key,
            response_format=SupervisorDecision
        )
        content = response.choices[0].message.content
        import json
        decision = json.loads(content)
        return {
            "routing_destination": decision.get("next_agent", "end")
        }
    except Exception:
        # Standard fallback to general advisor or end
        return {
            "routing_destination": "advisor_agent"
        }
