import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class GroundednessEvaluator:
    """
    Automated heuristic groundedness and factual claim evaluator for CareerOS.
    Compares generated LLM response claims against:
      - structured_resume_data (resume skills, companies, job titles, education)
      - job_description (target role requirements and qualifications)
      - retrieved_context (RAG retrieved passages)

    Note: This is an automated heuristic estimation tool, not perfect human fact verification.
    """

    def evaluate_groundedness(
        self,
        response_text: str,
        structured_resume_data: Optional[Dict[str, Any]] = None,
        job_description: Optional[str] = None,
        retrieved_context: Optional[List[str]] = None,
        user_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates whether claims in the response are grounded in the provided context sources.
        """
        if not response_text:
            return {
                "grounded": True,
                "unsupported_claims": [],
                "hallucination_risk": "low",
                "evaluation_notes": ["Empty response evaluated as grounded."],
            }

        unsupported_claims: List[str] = []
        notes: List[str] = [
            "Automated heuristic evaluation: claims parsed and checked against available context sources."
        ]

        response_lower = response_text.lower()

        # 1. Grounding check against Structured Resume Data
        if structured_resume_data:
            resume_unsupported = self._check_resume_grounding(response_text, structured_resume_data)
            unsupported_claims.extend(resume_unsupported)

        # 2. Grounding check against Job Description
        if job_description:
            jd_unsupported = self._check_jd_grounding(response_text, job_description)
            unsupported_claims.extend(jd_unsupported)

        # 3. Grounding check against RAG Context
        if retrieved_context:
            rag_unsupported = self._check_rag_grounding(response_text, retrieved_context, user_query)
            unsupported_claims.extend(rag_unsupported)

        # Remove duplicate claims
        unsupported_claims = list(set(unsupported_claims))

        # Risk Classification
        num_unsupported = len(unsupported_claims)
        if num_unsupported >= 3:
            hallucination_risk = "high"
            grounded = False
        elif num_unsupported >= 1:
            hallucination_risk = "medium"
            grounded = False
        else:
            hallucination_risk = "low"
            grounded = True

        if not grounded:
            notes.append(f"Detected {num_unsupported} potentially unsupported claim(s).")

        return {
            "grounded": grounded,
            "unsupported_claims": unsupported_claims,
            "hallucination_risk": hallucination_risk,
            "evaluation_notes": notes,
        }

    def _check_resume_grounding(
        self, response_text: str, resume_data: Dict[str, Any]
    ) -> List[str]:
        unsupported = []
        response_lower = response_text.lower()

        # Collect known resume entity tokens
        known_skills = {s.lower() for s in resume_data.get("skills", [])}
        known_companies = set()
        for exp in resume_data.get("experiences", []):
            if exp.get("company"):
                known_companies.add(exp["company"].lower())

        # Check for claims of specialized tech skills or company experience not in resume
        tech_claim_matches = re.findall(
            r"\b(proficient in|expert in|experienced with|worked at|employed by)\s+([A-Za-z0-9#\+\.]+)",
            response_lower
        )
        for indicator, entity in tech_claim_matches:
            clean_entity = entity.strip(".,;:").lower()
            if len(clean_entity) > 2 and clean_entity not in known_skills and clean_entity not in known_companies:
                # Exclude common stop words
                if clean_entity not in {"the", "a", "an", "this", "your", "my", "our", "their", "many", "various"}:
                    unsupported.append(f"Claimed experience with '{entity}' which is missing from structured resume data.")

        return unsupported

    def _check_jd_grounding(
        self, response_text: str, job_description: str
    ) -> List[str]:
        unsupported = []
        jd_lower = job_description.lower()

        # Check for specific job requirements claimed as mandatory that do not exist in JD
        jd_claims = re.findall(
            r"\b(job requires|must have|mandatory skill|required qualification)\s+is\s+([A-Za-z0-9#\+\.]+)",
            response_text.lower()
        )
        for _, skill in jd_claims:
            clean_skill = skill.strip(".,;:").lower()
            if len(clean_skill) > 2 and clean_skill not in jd_lower:
                unsupported.append(f"Claimed job requirement '{skill}' is absent from target job description.")

        return unsupported

    def _check_rag_grounding(
        self,
        response_text: str,
        retrieved_context: List[str],
        user_query: Optional[str]
    ) -> List[str]:
        unsupported = []
        context_corpus = " ".join(retrieved_context).lower()

        # Find specific factual statements (e.g. numeric metrics or dates claimed as retrieved context)
        metrics_in_response = re.findall(r"\b(\d+%\s+increase|\d+\s+years\s+experience|\$\d+k)\b", response_text.lower())
        for metric in metrics_in_response:
            if metric not in context_corpus:
                unsupported.append(f"Metric '{metric}' stated in RAG response is not present in retrieved context.")

        return unsupported
