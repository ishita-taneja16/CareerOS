"""
CrewAI Demonstration Module for CareerOS.
Isolated comparison prototype for resume analysis and ATS keyword feedback.
Existing LangGraph implementation remains the primary production orchestrator.
"""

from .tools import ats_keyword_match_tool, resume_bullet_auditor_tool
from .crew_app import build_resume_analysis_crew, run_resume_analysis_crew

__all__ = [
    "ats_keyword_match_tool",
    "resume_bullet_auditor_tool",
    "build_resume_analysis_crew",
    "run_resume_analysis_crew",
]
