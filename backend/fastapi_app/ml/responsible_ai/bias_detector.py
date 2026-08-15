import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Sensitive terms and stereotyping patterns to evaluate in career platform responses
GENDER_BIAS_PATTERNS = [
    (r"\b(he|his|him)\s+is\s+suited\s+for\s+(management|leadership|executive|tech|engineering)\b", "Gender stereotyping in role recommendation"),
    (r"\b(she|her)\s+is\s+suited\s+for\s+(admin|support|hr|nursing)\b", "Gender stereotyping in role recommendation"),
    (r"\bmale-dominated\s+role\b", "Potentially discouraging gender-typed phrasing"),
    (r"\bfemale-oriented\s+field\b", "Potentially discouraging gender-typed phrasing"),
]

AGE_BIAS_PATTERNS = [
    (r"\btoo\s+(old|senior|experienced)\s+to\s+learn\b", "Ageist capability assumption"),
    (r"\bdigital\s+native\s+only\b", "Age-discriminatory qualification phrasing"),
    (r"\byoung\s+and\s+energetic\b", "Ageist descriptor in candidate criteria"),
]

PROTECTED_CLASS_PATTERNS = [
    (r"\bnative\s+english\s+speaker\s+only\b", "Potential national origin discrimination"),
    (r"\bcandidate\s+ethnicity\b", "Unrelated protected demographic consideration"),
]


class BiasDetector:
    """
    Evaluates input prompts and candidate-facing agent outputs for demographic,
    gender, age, and discriminatory bias in career advice and resume evaluation.
    """

    def __init__(self, threshold: float = 0.15):
        self.threshold = threshold

    def analyze_text(self, text: str) -> Dict[str, Any]:
        if not text:
            return {
                "has_bias": False,
                "bias_score": 0.0,
                "detected_categories": [],
                "warnings": [],
            }

        text_lower = text.lower()
        warnings: List[str] = []
        categories: List[str] = []
        score = 0.0

        # Check Gender Patterns
        for pattern, desc in GENDER_BIAS_PATTERNS:
            if re.search(pattern, text_lower):
                warnings.append(f"Gender Bias Warning: {desc}")
                if "gender" not in categories:
                    categories.append("gender")
                score += 0.25

        # Check Age Patterns
        for pattern, desc in AGE_BIAS_PATTERNS:
            if re.search(pattern, text_lower):
                warnings.append(f"Age Bias Warning: {desc}")
                if "age" not in categories:
                    categories.append("age")
                score += 0.25

        # Check Protected Class Patterns
        for pattern, desc in PROTECTED_CLASS_PATTERNS:
            if re.search(pattern, text_lower):
                warnings.append(f"Protected Class Bias Warning: {desc}")
                if "protected_class" not in categories:
                    categories.append("protected_class")
                score += 0.30

        bias_score = min(round(score, 2), 1.0)
        has_bias = bias_score > self.threshold

        if has_bias:
            logger.warning(
                f"BiasDetector triggered | Score: {bias_score} | Categories: {categories}"
            )

        return {
            "has_bias": has_bias,
            "bias_score": bias_score,
            "detected_categories": categories,
            "warnings": warnings,
        }
