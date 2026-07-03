from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.supervisor import run_supervisor
from agents.resume_agent import run_resume_agent
from agents.ats_agent import run_ats_agent
from agents.memory_agent import run_memory_agent
from agents.interview_agent import run_interview_agent
from agents.advisor_agent import run_advisor_agent
from agents.cover_letter_agent import run_cover_letter_agent
from agents.skill_gap_agent import run_skill_gap_agent

def run_pipeline_dispatcher(state: AgentState) -> dict:
    """
    Dispatcher node. Pops the next scheduled agent from the routing_pipeline
    and sets routing_destination. If pipeline is empty, routes to END.
    """
    pipeline = state.get("routing_pipeline", []) if isinstance(state, dict) else getattr(state, "routing_pipeline", [])
    pipeline = list(pipeline)  # Make a copy to prevent mutations

    if pipeline:
        next_agent = pipeline.pop(0)
        return {
            "routing_pipeline": pipeline,
            "routing_destination": next_agent
        }
    else:
        return {
            "routing_destination": "end"
        }

def create_graph():
    workflow = StateGraph(AgentState)
    
    # Register Nodes
    workflow.add_node("supervisor", run_supervisor)
    workflow.add_node("pipeline_dispatcher", run_pipeline_dispatcher)
    workflow.add_node("resume_agent", run_resume_agent)
    workflow.add_node("ats_agent", run_ats_agent)
    workflow.add_node("memory_agent", run_memory_agent)
    workflow.add_node("interview_agent", run_interview_agent)
    workflow.add_node("advisor_agent", run_advisor_agent)
    workflow.add_node("cover_letter_agent", run_cover_letter_agent)
    workflow.add_node("skill_gap_agent", run_skill_gap_agent)
    
    # Entry point routes directly to supervisor
    workflow.set_entry_point("supervisor")
    
    # Supervisor outputs the pipeline list and routes to dispatcher
    workflow.add_edge("supervisor", "pipeline_dispatcher")
    
    # Dispatcher inspects pipeline and routes conditionally
    def route_from_dispatcher(state: AgentState) -> str:
        dest = state.get("routing_destination", "end") if isinstance(state, dict) else getattr(state, "routing_destination", "end")
        if dest in [
            "resume_agent", "ats_agent", "memory_agent", "interview_agent",
            "advisor_agent", "cover_letter_agent", "skill_gap_agent"
        ]:
            return dest
        return END

    workflow.add_conditional_edges(
        "pipeline_dispatcher",
        route_from_dispatcher,
        {
            "resume_agent": "resume_agent",
            "ats_agent": "ats_agent",
            "memory_agent": "memory_agent",
            "interview_agent": "interview_agent",
            "advisor_agent": "advisor_agent",
            "cover_letter_agent": "cover_letter_agent",
            "skill_gap_agent": "skill_gap_agent",
            "end": END
        }
    )
    
    # Worker nodes route back to dispatcher to check if more nodes need execution
    workflow.add_edge("resume_agent", "pipeline_dispatcher")
    workflow.add_edge("ats_agent", "pipeline_dispatcher")
    workflow.add_edge("memory_agent", "pipeline_dispatcher")
    workflow.add_edge("interview_agent", "pipeline_dispatcher")
    workflow.add_edge("advisor_agent", "pipeline_dispatcher")
    workflow.add_edge("cover_letter_agent", "pipeline_dispatcher")
    workflow.add_edge("skill_gap_agent", "pipeline_dispatcher")
    
    return workflow.compile()

compiled_graph = create_graph()
