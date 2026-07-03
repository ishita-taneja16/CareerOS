from agents.state import AgentState
from core.logging_decorator import agent_logger
from services.ats_service import ATSEngine

ats_engine = ATSEngine()

@agent_logger("ats_agent")
def run_ats_agent(state: AgentState) -> dict:
    """
    ATSAgent. Runs custom NLP calculations and explains recommendations.
    """
    resume_json = state.get("structured_resume_data") if isinstance(state, dict) else getattr(state, "structured_resume_data", None)
    jd = state.get("job_description") if isinstance(state, dict) else getattr(state, "job_description", None)

    if not resume_json or not jd:
        return {
            "last_response": "Please upload your resume and provide a Job Description to run the ATS Audit.",
            "routing_destination": "pipeline_dispatcher"
        }

    from models.resume_schema import ResumeSchema
    resume_obj = ResumeSchema(**resume_json)
    results = ats_engine.analyze(resume_obj, jd)

    # Format feedback report
    sub = results['subscores']
    report = f"""
### 📊 ATS Audit Feedback Report
**Overall ATS Score**: {results['ats_score']}/100
**Expected ATS Improvement**: {results['expected_ats_improvement']} after resolving priority improvements.

#### Subscores:
- Keyword Match: {sub['keyword_match']}%
- Skill Match: {sub['skill_match']}%
- Semantic Alignment: {sub['semantic_similarity']}%
- Active Verbs Compliance: {sub['action_verbs']}%
- Quantified Achievements: {sub['quantified_achievements']}%
- Formatting Quality: {sub['formatting_score']}%
- Grammar Quality: {sub['grammar_quality']}%
- Experience Relevance: {sub['experience_relevance']}%
- Project Relevance: {sub['project_relevance']}%
- Education Relevance: {sub['education_relevance']}%

#### Key Strengths:
""" + "\n".join([f"- {s}" for s in results['strengths']]) + """

#### Areas of Weakness:
""" + "\n".join([f"- {w}" for w in results['weaknesses']]) + """

#### Missing Skills:
""" + (", ".join(results['missing_skills'][:6]) if results['missing_skills'] else "None") + """

#### Missing Keywords:
""" + (", ".join(results['missing_keywords'][:6]) if results['missing_keywords'] else "None") + """

#### Priority Recommendations:
""" + "\n".join([f"- {p}" for p in results['priority_suggestions']])

    return {
        "ats_results": results,
        "last_response": report.strip(),
        "routing_destination": "pipeline_dispatcher"
    }
