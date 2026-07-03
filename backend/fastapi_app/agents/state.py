from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    user_id: str
    active_resume_version_id: Optional[str] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list) # Chat history
    job_description: Optional[str] = None
    routing_destination: str = "supervisor"
    routing_pipeline: List[str] = Field(default_factory=list) # List of agent names scheduled to execute in sequence
    structured_resume_data: Optional[Dict[str, Any]] = None # Temp holder for changes
    ats_results: Optional[Dict[str, Any]] = None
    interview_session_id: Optional[str] = None
    last_response: Optional[str] = None
