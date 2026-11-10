import re
from typing import Dict, Any, List
from crewai.tools import tool


@tool("ATS Keyword Match Tool")
def ats_keyword_match_tool(resume_text: str, target_keywords: str) -> str:
    """
    Computes keyword alignment percentage and missing skills between resume text and required skills.
    target_keywords should be a comma-separated list of target technical skills.
    """
    if not resume_text or not target_keywords:
        return "Invalid input: resume text and target keywords are required."

    original_keywords = [k.strip() for k in target_keywords.split(",") if k.strip()]
    resume_lower = resume_text.lower()

    matched = []
    missing = []

    for orig_kw in original_keywords:
        pattern = r"\b" + re.escape(orig_kw.lower()) + r"\b"
        if re.search(pattern, resume_lower):
            matched.append(orig_kw)
        else:
            missing.append(orig_kw)

    total = len(original_keywords)
    score = (len(matched) / total * 100.0) if total > 0 else 0.0

    return (
        f"ATS Keyword Analysis:\n"
        f"- Match Score: {score:.1f}%\n"
        f"- Matched Keywords ({len(matched)}): {', '.join(matched) if matched else 'None'}\n"
        f"- Missing Keywords ({len(missing)}): {', '.join(missing) if missing else 'None'}"
    )


@tool("Resume Bullet Point Action Verb Auditor")
def resume_bullet_auditor_tool(bullet_points: str) -> str:
    """
    Analyzes resume bullet points for strong action verbs and quantified impact metrics.
    bullet_points should be newline-separated bullet text.
    """
    strong_action_verbs = {
        "architected", "engineered", "optimized", "spearheaded", "developed",
        "implemented", "accelerated", "reduced", "scaled", "orchestrated",
        "designed", "streamlined", "automated", "mentored", "delivered"
    }

    bullets = [b.strip().lstrip("-•* ") for b in bullet_points.split("\n") if b.strip()]
    if not bullets:
        return "No bullet points provided for audit."

    weak_bullets = []
    strong_bullets = []

    for bullet in bullets:
        first_word = bullet.split()[0].lower() if bullet.split() else ""
        has_metric = bool(re.search(r"\d+[%kKmMxX]?|\$\d+", bullet))
        has_strong_verb = first_word in strong_action_verbs

        if has_strong_verb and has_metric:
            strong_bullets.append(bullet)
        else:
            weak_bullets.append(bullet)

    return (
        f"Bullet Audit Report:\n"
        f"- Total Bullets Evaluated: {len(bullets)}\n"
        f"- High-Impact Bullets (Strong Verb + Quantified Metric): {len(strong_bullets)}\n"
        f"- Needs Improvement: {len(weak_bullets)}\n"
        f"- Recommendation: Ensure each bullet starts with a past-tense action verb and includes measurable ROI."
    )
