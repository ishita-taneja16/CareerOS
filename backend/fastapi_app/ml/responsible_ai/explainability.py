from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ExplainabilityEngine:
    """
    Generates explainability metadata, confidence metrics, and audit traces for
    career model predictions, ATS scoring decisions, and recommendation rationale.
    """

    @staticmethod
    def generate_ats_explanation(
        ats_score: float,
        keyword_matches: List[str],
        missing_keywords: List[str],
        section_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Provides transparent breakdown of how ATS score was calculated.
        """
        matched_count = len(keyword_matches)
        missing_count = len(missing_keywords)
        total_keywords = matched_count + missing_count
        keyword_ratio = (matched_count / total_keywords) if total_keywords > 0 else 0.0

        confidence = round(min(0.5 + 0.5 * (total_keywords / 10.0), 0.99), 2)

        reasoning = (
            f"ATS Score of {ats_score}/100 is based on keyword coverage of "
            f"{matched_count}/{total_keywords} required competencies "
            f"({round(keyword_ratio * 100, 1)}%) combined with section formatting scores."
        )

        return {
            "ats_score": ats_score,
            "confidence_score": confidence,
            "reasoning_summary": reasoning,
            "feature_attribution": {
                "keyword_coverage_percent": round(keyword_ratio * 100, 1),
                "matched_keywords_count": matched_count,
                "missing_keywords_count": missing_count,
                "section_scores": section_scores,
            },
            "audit_trail": {
                "source": "CareerOS Rule-Based & Semantic Evaluator",
                "explainability_version": "1.0",
            },
        }

    @staticmethod
    def audit_agent_decision(
        agent_name: str,
        decision_reason: str,
        user_prompt: str
    ) -> Dict[str, Any]:
        """
        Audits supervisor routing decisions for user transparency.
        """
        return {
            "selected_agent": agent_name,
            "decision_reason": decision_reason,
            "user_prompt_summary": user_prompt[:100] + "..." if len(user_prompt) > 100 else user_prompt,
            "explainability_type": "Routing Rationale",
        }
