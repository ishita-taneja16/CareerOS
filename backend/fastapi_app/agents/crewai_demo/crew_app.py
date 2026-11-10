"""
CrewAI Demonstration Prototype for CareerOS.
Isolated prototype comparing role-based agent crew orchestration with the primary LangGraph implementation.
"""

import os
import sys
from typing import Dict, Any, Optional

# Align python path and opt out of network telemetry
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, Process
from agents.crewai_demo.tools import ats_keyword_match_tool, resume_bullet_auditor_tool
from config import settings


def build_resume_analysis_crew(llm=None, verbose: bool = False) -> Crew:
    """
    Constructs an isolated 2-agent Crew for resume analysis and ATS keyword feedback.
    1. Resume Analyst Agent: Audits structural quality and quantified accomplishments.
    2. ATS Keyword Specialist Agent: Scores keyword density and recommends additions.
    """
    # 1. Define Specialized Agents
    resume_analyst = Agent(
        role="Senior Technical Resume Reviewer",
        goal="Audit candidate resume sections, bullet points, and impact metrics for engineering roles.",
        backstory=(
            "You are a seasoned Principal Engineer and hiring manager with 15+ years of experience "
            "evaluating software and AI engineering resumes at top tech firms."
        ),
        tools=[resume_bullet_auditor_tool],
        llm=llm,
        verbose=verbose,
        allow_delegation=False,
    )

    ats_specialist = Agent(
        role="Applicant Tracking System (ATS) Specialist",
        goal="Optimize candidate keyword alignment and section readability to maximize ATS pass rates.",
        backstory=(
            "You are an expert recruiter and ATS algorithm specialist who understands semantic indexing, "
            "parser tokenization, and keyword matching heuristics."
        ),
        tools=[ats_keyword_match_tool],
        llm=llm,
        verbose=verbose,
        allow_delegation=False,
    )

    # 2. Define Sequential Tasks
    task_structure_audit = Task(
        description=(
            "Analyze the provided resume text:\n"
            "{resume_text}\n\n"
            "Target role: {target_role}\n"
            "Use the Resume Bullet Point Action Verb Auditor tool to evaluate bullet points. "
            "Identify strong bullets with metrics and weak bullets that lack quantifiable impact."
        ),
        expected_output=(
            "A structured audit highlighting 3 key strengths and 3 concrete bullet point rewrites "
            "following the Action Verb + Context + Quantified Metric formula."
        ),
        agent=resume_analyst,
    )

    task_ats_optimization = Task(
        description=(
            "Evaluate keyword density and ATS alignment for the target keywords:\n"
            "{target_keywords}\n\n"
            "Use the ATS Keyword Match Tool to compute match score and identify missing technical competencies. "
            "Suggest natural, contextual placements for missing keywords in the resume."
        ),
        expected_output=(
            "An ATS optimization report with match percentage, missing critical keywords, "
            "and recommended additions organized by experience/project sections."
        ),
        agent=ats_specialist,
    )

    # 3. Assemble Sequential Crew
    crew = Crew(
        agents=[resume_analyst, ats_specialist],
        tasks=[task_structure_audit, task_ats_optimization],
        process=Process.sequential,
        verbose=verbose,
    )

    return crew


def run_resume_analysis_crew(
    resume_text: str,
    target_role: str = "Senior AI Engineer",
    target_keywords: str = "FastAPI, LangGraph, Langfuse, PostgreSQL, ChromaDB, PyTorch",
    llm=None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Executes the isolated CrewAI demo workflow.
    Returns structured results comparing inputs and outputs.
    Note: Prototype for comparison; primary production system uses LangGraph.
    """
    crew = build_resume_analysis_crew(llm=llm, verbose=verbose)
    inputs = {
        "resume_text": resume_text,
        "target_role": target_role,
        "target_keywords": target_keywords,
    }

    raw_output = crew.kickoff(inputs=inputs)

    return {
        "framework": "CrewAI",
        "prototype_type": "Comparison Demonstration",
        "target_role": target_role,
        "inputs": inputs,
        "crew_output": str(raw_output),
        "status": "completed",
    }
