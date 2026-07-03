from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
from agents.graph import compiled_graph
from agents.state import AgentState
from services.db_service import fetch_active_resume_from_db

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_id: str
    messages: List[ChatMessage]
    active_resume_version_id: Optional[str] = None
    job_description: Optional[str] = None
    structured_resume_data: Optional[Dict[str, Any]] = None

@router.post("/")
async def chat_interaction(request: ChatRequest):
    """
    Submit chat messages history and run the supervisor-led multi-agent Graph.
    Streams execution steps and text responses.
    """
    # 1. Resolve active resume data
    resume_data = request.structured_resume_data
    if not resume_data:
        resume_data = await fetch_active_resume_from_db(request.user_id)

    # 2. Build initial LangGraph state inputs
    messages_dict = [{"role": m.role, "content": m.content} for m in request.messages]
    initial_state = AgentState(
        user_id=request.user_id,
        active_resume_version_id=request.active_resume_version_id,
        messages=messages_dict,
        job_description=request.job_description,
        structured_resume_data=resume_data
    )

    async def sse_generator():
        try:
            # We run compiled_graph.astream asynchronously to yield steps
            # Since LangGraph execution returns node outputs on each step:
            # e.g., {'supervisor': {'routing_destination': 'resume_agent'}}
            async for step in compiled_graph.astream(initial_state.model_dump()):
                for node_name, node_output in step.items():
                    # Send step progress events
                    yield f"event: step\ndata: {json.dumps({'node': node_name, 'routing': node_output.get('routing_destination', '')})}\n\n"
                    
                    # Yield final agent texts if produced
                    if "last_response" in node_output and node_output["last_response"]:
                        yield f"event: message\ndata: {json.dumps({'text': node_output['last_response']})}\n\n"
                        
                    await asyncio.sleep(0.1)
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
