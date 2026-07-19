import json
from typing import Dict, Any, List
# pyrefly: ignore [missing-import]
from litellm import completion
from config import settings
from agents.state import AgentState
from services.ats_service import ATSEngine
from services.vector_service import VectorStoreService

ats_engine = ATSEngine()
vector_store = VectorStoreService()

def run_resume_agent(state: AgentState) -> dict:
    """
    ResumeAgent. Modifies structure of active resume JSON data and writes descriptions.
    """
    latest_user_message = state.messages[-1]["content"] if state.messages else ""
    resume_json = state.structured_resume_data or {}
    
    prompt = f"""
You are the Resume Agent. Your job is to modify structured resume JSON according to the user's instructions.
Modify ONLY the fields requested. Keep formatting standard. Preserve all other existing fields exactly.
Provide the output in valid JSON matching the format of the input.

User instruction: "{latest_user_message}"

Current Resume JSON:
---
{json.dumps(resume_json, indent=2)}
---
"""

    model = "gemini/gemini-2.5-flash" if settings.GEMINI_API_KEY else "ollama/llama3"
    api_key = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY else None

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        modified_resume = json.loads(content)
        # We save this inside the state as well as return the textual confirmation
        return {
            "structured_resume_data": modified_resume,
            "last_response": "I've successfully updated your resume data. You can view the modified version in the editor pane.",
            "routing_destination": "supervisor"
        }
    except Exception as e:
        return {
            "last_response": f"Failed to modify the resume: {str(e)}",
            "routing_destination": "supervisor"
        }


def run_ats_agent(state: AgentState) -> dict:
    """
    ATSAgent. Runs custom NLP calculations and explains recommendations.
    """
    if not state.structured_resume_data or not state.job_description:
        return {
            "last_response": "Please upload your resume and provide a Job Description to run the ATS Audit.",
            "routing_destination": "supervisor"
        }

    from models.resume_schema import ResumeSchema
    resume_obj = ResumeSchema(**state.structured_resume_data)
    results = ats_engine.analyze(resume_obj, state.job_description)

    # Format feedback report cleanly for user read
    report = f"""
### 📊 ATS Audit Feedback Report
**Overall ATS Score**: {results['ats_score']}/100

#### Subscores:
- Keyword Match: {results['subscores']['keyword_match']}%
- Semantic Alignment: {results['subscores']['semantic_similarity']}%
- Active Verbs compliance: {results['subscores']['action_verbs']}%
- Structure/Formatting: {results['subscores']['formatting_score']}%
- Experience match: {results['subscores']['experience_match']}%

#### Key Strengths:
""" + "\n".join([f"- {s}" for s in results['strengths']]) + """

#### Areas of Weakness:
""" + "\n".join([f"- {w}" for w in results['weaknesses']]) + """

#### Priority Recommendations:
""" + "\n".join([f"- {p}" for p in results['priority_suggestions']])

    return {
        "ats_results": results,
        "last_response": report.strip(),
        "routing_destination": "supervisor"
    }


def run_cover_letter_agent(state: AgentState) -> dict:
    """
    CoverLetterAgent. Drafts targeted cover letters.
    """
    if not state.structured_resume_data:
        return {
            "last_response": "I need your resume details to draft a cover letter. Please upload a resume first.",
            "routing_destination": "supervisor"
        }

    resume_json = state.structured_resume_data
    jd = state.job_description or "General software engineering role."

    prompt = f"""
You are the Cover Letter Agent. Draft a tailored, professional, and impact-driven cover letter for the role described in the Job Description, leveraging the Candidate's Resume.
Keep it strictly under 400 words. Highlight accomplishments matching the requirements using a premium professional tone.

Job Description:
{jd}

Candidate Resume:
{json.dumps(resume_json, indent=2)}
"""

    model = "gemini/gemini-2.5-flash" if settings.GEMINI_API_KEY else "ollama/llama3"
    api_key = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY else None

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key
        )
        cover_letter = response.choices[0].message.content
        return {
            "last_response": cover_letter.strip(),
            "routing_destination": "supervisor"
        }
    except Exception as e:
        return {
            "last_response": f"Failed to generate cover letter: {str(e)}",
            "routing_destination": "supervisor"
        }


def run_interview_agent(state: AgentState) -> dict:
    """
    InterviewAgent. Conducts mock interview simulations.
    """
    latest_user_message = state.messages[-1]["content"] if state.messages else ""
    jd = state.job_description or "Software Engineering Generalist Role"
    history = [m for m in state.messages if m.get("role") != "system"]

    # Prompt design to act as a simulated technical recruiter
    prompt = f"""
You are a Simulated Tech Recruiter conducting a mock interview.
Your goal is to evaluate the candidate's answers based on communication, technical accuracy, and the STAR format.

Role context (Job Description):
---
{jd}
---

Candidate Resume:
---
{json.dumps(state.structured_resume_data, indent=2)}
---

Interview History:
{json.dumps(history[-8:], indent=2)}

Candidate reply: "{latest_user_message}"

If the interview is just beginning (no previous questions/answers in history), welcome the candidate and ask the first behavioral or technical question.
Otherwise:
1. Provide short feedback on their answer.
2. Ask the next question (mix coding, system design, and HR/behavioral).
3. If they ask to end the interview, output a structured final rating feedback (overall rating 1-5, strengths, areas of improvement).
"""

    model = "gemini/gemini-2.5-flash" if settings.GEMINI_API_KEY else "ollama/llama3"
    api_key = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY else None

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key
        )
        recruiter_reply = response.choices[0].message.content
        return {
            "last_response": recruiter_reply.strip(),
            "routing_destination": "supervisor"
        }
    except Exception as e:
        return {
            "last_response": f"Interview simulator encounterd an error: {str(e)}",
            "routing_destination": "supervisor"
        }


def run_skill_gap_agent(state: AgentState) -> dict:
    """
    SkillGapAgent. Identifies knowledge gap roadmaps.
    """
    if not state.structured_resume_data or not state.job_description:
        return {
            "last_response": "I need your resume details and the target Job Description to run a Skill Gap Analysis.",
            "routing_destination": "supervisor"
        }

    resume_skills = state.structured_resume_data.get("skills", [])
    jd = state.job_description

    prompt = f"""
You are the Skill Gap Agent. Analyze the candidate's skills against the Job Description.
Identify missing technical skills, frameworks, and domain knowledge.
Provide:
1. List of missing skills.
2. An estimated learning roadmap (split into weeks/phases).
3. Suggested practical projects to learn these skills.
4. Estimated study time needed in total.

Candidate Skills:
{", ".join(resume_skills)}

Job Description:
{jd}
"""

    model = "gemini/gemini-2.5-flash" if settings.GEMINI_API_KEY else "ollama/llama3"
    api_key = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY else None

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key
        )
        roadmap = response.choices[0].message.content
        return {
            "last_response": roadmap.strip(),
            "routing_destination": "supervisor"
        }
    except Exception as e:
        return {
            "last_response": f"Failed to perform skill gap analysis: {str(e)}",
            "routing_destination": "supervisor"
        }


def run_advisor_agent(state: AgentState) -> dict:
    """
    CareerAdvisorAgent. Handles general guidance, searches memory RAG.
    """
    latest_user_message = state.messages[-1]["content"] if state.messages else ""
    user_id = state.user_id

    # 1. Fetch relevant user memories from vector store
    memories = vector_store.query_memories(user_id, latest_user_message, limit=3)
    memory_context = "\n".join([f"- Preference ({m['category']}): {m['text']}" for m in memories])

    prompt = f"""
You are the Career Advisor Agent. You have access to the user's historical preferences and profile goals.
Help the user answer general career questions, prepare strategy, or suggest steps.

Candidate Profile Summary:
{json.dumps(state.structured_resume_data, indent=2) if state.structured_resume_data else "No active resume uploaded yet."}

User preferences recalled from long term memory:
{memory_context if memory_context else "None recorded yet."}

User request: "{latest_user_message}"
"""

    model = "gemini/gemini-2.5-flash" if settings.GEMINI_API_KEY else "ollama/llama3"
    api_key = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY else None

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key
        )
        advisor_reply = response.choices[0].message.content

        # 2. Extract facts asynchronously to feed memory
        # We search if the user stated any preferences like "I prefer remote" or "I want to work in San Francisco"
        # and store it in vector memory
        _capture_memories(user_id, latest_user_message, model, api_key)

        return {
            "last_response": advisor_reply.strip(),
            "routing_destination": "supervisor"
        }
    except Exception as e:
        return {
            "last_response": f"Career advisor encountered an error: {str(e)}",
            "routing_destination": "supervisor"
        }


def _capture_memories(user_id: str, message: str, model: str, api_key: Optional[str]) -> None:
    """Helper to detect facts/preferences in conversation and save them in ChromaDB."""
    prompt = f"""
Identify if the user is stating a long-term personal preference, experience, certification, or goal in the text.
If yes, summarize it into a concise single statement.
Output ONLY the statement or empty string if no core fact was stated.

User message: "{message}"
"""
    try:
        res = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key
        )
        fact = res.choices[0].message.content.strip()
        if fact and len(fact) > 5 and not fact.startswith("No"):
            # Determine category
            category = "preference"
            if "skill" in message.lower() or "learn" in message.lower():
                category = "skill"
            elif "experience" in message.lower() or "worked" in message.lower():
                category = "experience"
            
            vector_store.add_memory(user_id, fact, category)
    except Exception:
        pass
