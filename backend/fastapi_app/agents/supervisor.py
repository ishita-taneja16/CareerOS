from pydantic import BaseModel, Field
from litellm import completion
from config import settings
from agents.state import AgentState
import json


class SupervisorDecision(BaseModel):
    next_agent: str = Field(
        description=(
            "The next agent to route the conversation to: "
            "resume_agent, ats_agent, interview_agent, "
            "cover_letter_agent, skill_gap_agent, "
            "memory_agent, advisor_agent, or end"
        )
    )
    reason: str = Field(
        description="Short rationale explaining the routing decision"
    )


def run_supervisor(state: AgentState) -> dict:
    """
    Supervisor node.
    Reads the latest conversation and decides which agent
    should execute next.
    """

    history = []

    for msg in state.messages[-5:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history.append(f"{role.capitalize()}: {content}")

    history_str = "\n".join(history)

    prompt = f"""
You are the Supervisor Agent for an AI Career Copilot.

Choose ONLY ONE next specialist agent.

Available agents:

- resume_agent
- ats_agent
- interview_agent
- cover_letter_agent
- skill_gap_agent
- memory_agent
- advisor_agent
- end

Conversation:

{history_str}

Return ONLY valid JSON.

Example:

{{
    "next_agent": "advisor_agent",
    "reason": "General career advice"
}}
"""

    model = (
        "gemini/gemini-2.5-flash"
        if settings.GEMINI_API_KEY
        else "ollama/llama3"
    )

    api_key = settings.GEMINI_API_KEY or None

    try:
        response = completion(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            api_key=api_key,
            response_format=SupervisorDecision,
        )

        decision = json.loads(response.choices[0].message.content)

        next_agent = decision.get("next_agent", "advisor_agent")

        if next_agent == "end":
            pipeline = []
        else:
            pipeline = [next_agent]

        return {
            "routing_destination": next_agent,
            "routing_pipeline": pipeline,
        }

    except Exception:
        return {
            "routing_destination": "advisor_agent",
            "routing_pipeline": ["advisor_agent"],
        }