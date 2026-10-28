import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Align python path and opt out of network/telemetry fetches.
# LITELLM_LOCAL_MODEL_COST_MAP must be set before litellm is imported
# (transitively via agents.*) to avoid a ~90 s SSL-handshake timeout.
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from agents.crewai_demo.tools import ats_keyword_match_tool, resume_bullet_auditor_tool
from agents.crewai_demo.crew_app import build_resume_analysis_crew, run_resume_analysis_crew
from agents.graph import compiled_graph


def test_ats_keyword_match_tool():
    """Verify ATS keyword match tool calculates overlap percentages and flags missing terms."""
    resume_text = "Experienced Senior Engineer proficient in Python, FastAPI, PostgreSQL, and Docker."
    keywords = "FastAPI, PostgreSQL, Redis, Kubernetes, Docker"

    result = ats_keyword_match_tool.run(resume_text=resume_text, target_keywords=keywords)

    assert "ATS Keyword Analysis" in result
    assert "FastAPI" in result
    assert "PostgreSQL" in result
    assert "Redis" in result
    assert "Kubernetes" in result
    # 3 matched (FastAPI, PostgreSQL, Docker) out of 5 = 60.0%
    assert "60.0%" in result


def test_resume_bullet_auditor_tool():
    """Verify bullet auditor tool recognizes action verbs and metric patterns."""
    bullets = (
        "Architected high-throughput FastAPI microservice reducing latency by 45%.\n"
        "Helped team with some frontend tasks.\n"
        "Optimized PostgreSQL queries, saving $12,000 annually in database costs."
    )

    result = resume_bullet_auditor_tool.run(bullet_points=bullets)

    assert "Bullet Audit Report" in result
    assert "Total Bullets Evaluated: 3" in result
    assert "High-Impact Bullets (Strong Verb + Quantified Metric): 2" in result
    assert "Needs Improvement: 1" in result


def test_build_resume_analysis_crew_structure():
    """Verify agents and tasks are assembled correctly without launching live LLM calls."""
    crew = build_resume_analysis_crew(llm=None, verbose=False)

    assert len(crew.agents) == 2
    assert crew.agents[0].role == "Senior Technical Resume Reviewer"
    assert crew.agents[1].role == "Applicant Tracking System (ATS) Specialist"
    assert len(crew.tasks) == 2


def test_run_resume_analysis_crew_mocked():
    """Verify run_resume_analysis_crew executes and formats return dictionary with mock."""
    mock_crew = MagicMock()
    mock_crew.kickoff.return_value = "Mocked CrewAI Analysis Output: High alignment with Senior AI Engineer role."

    with patch("agents.crewai_demo.crew_app.build_resume_analysis_crew", return_value=mock_crew):
        result = run_resume_analysis_crew(
            resume_text="Senior AI Engineer with 6 years experience in Python and PyTorch.",
            target_role="Senior AI Engineer",
            target_keywords="Python, PyTorch, LangGraph"
        )

        assert result["framework"] == "CrewAI"
        assert result["status"] == "completed"
        assert "Mocked CrewAI Analysis Output" in result["crew_output"]
        mock_crew.kickoff.assert_called_once()


def test_langgraph_intact_and_unaffected():
    """Verify existing LangGraph workflow is completely intact and functional."""
    assert compiled_graph is not None
    # Verify LangGraph compiled nodes
    nodes = compiled_graph.nodes
    assert "supervisor" in nodes
    assert "pipeline_dispatcher" in nodes
    assert "resume_agent" in nodes
    assert "ats_agent" in nodes
    assert "advisor_agent" in nodes
