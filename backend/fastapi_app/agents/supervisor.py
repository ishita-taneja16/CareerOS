import json
from pydantic import BaseModel, Field

from config import settings
from agents.state import AgentState
from services.llm_service import LLMService


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

    messages = (
        state.get("messages", [])
        if isinstance(state, dict)
        else getattr(state, "messages", [])
    )

    for msg in messages[-5:]:
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

    try:
        response = LLMService.call(
            prompt=prompt,
            response_format=SupervisorDecision,
        )

        decision = json.loads(response)

        next_agent = decision.get("next_agent", "advisor_agent")

        pipeline = [] if next_agent == "end" else [next_agent]

        return {
            "routing_destination": next_agent,
            "routing_pipeline": pipeline,
        }

    except Exception:
        return {
            "routing_destination": "advisor_agent",
            "routing_pipeline": ["advisor_agent"],
        }