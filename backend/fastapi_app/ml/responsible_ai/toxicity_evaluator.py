import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Heuristic pattern definitions for fallback local toxicity evaluation
TOXICITY_PATTERNS = {
    "threat": [
        r"\b(kill|harm|attack|destroy|hurt|injure|assassinate|stab|shoot)\s+(?:a|an|the|my|your|our|their|this)?\s*(you|them|him|her|candidate|recruiter)\b",
        r"\bdeath\s+threat\b",
    ],
    "insult": [
        r"\b(idiot|fool|stupid|dumb|moron|worthless|useless|incompetent|trash|garbage|loser)\b",
    ],
    "identity_attack": [
        r"\b(hate|disgusting|inferior|subhuman)\s+(?:a|an|the|my|your|our|their|this)?\s*(race|gender|religion|ethnic|disability|sexuality)\b",
        r"\bdiscriminatory\s+slur\b",
    ],
    "sexual_explicit": [
        r"\b(explicit|pornographic|nude|nsfw)\s+content\b",
    ],
    "toxicity": [
        r"\b(abusive|hateful|harass|harassment|hostile|toxic)\b",
    ],
}


class ToxicityEvaluator:
    """
    Local Detoxify-based & heuristic toxicity evaluator.
    Evaluates text for toxicity categories: toxicity, severe_toxicity, insult, threat, identity_attack, sexual_explicit.
    Classifies outputs as SAFE, REVIEW, or UNSAFE based on configurable thresholds.
    Free, local, and requires zero external/paid APIs.
    """

    def __init__(
        self,
        review_threshold: float = 0.30,
        unsafe_threshold: float = 0.60,
        use_detoxify_model: bool = True
    ):
        self.review_threshold = review_threshold
        self.unsafe_threshold = unsafe_threshold
        self.detoxify_model = None

        if use_detoxify_model:
            try:
                from detoxify import Detoxify
                # Load lightweight local Detoxify model if installed & cached
                self.detoxify_model = Detoxify('original')
                logger.info("Detoxify model initialized successfully.")
            except Exception as e:
                logger.debug(f"Detoxify model initialization skipped: {e}. Using local heuristic evaluator.")

    def evaluate_text(self, text: str) -> Dict[str, Any]:
        """
        Evaluates text and returns structured toxicity scores and classification.
        """
        if not text:
            scores = {
                "toxicity": 0.0,
                "severe_toxicity": 0.0,
                "insult": 0.0,
                "threat": 0.0,
                "identity_attack": 0.0,
                "sexual_explicit": 0.0,
            }
            return {
                "scores": scores,
                "classification": "SAFE",
                "max_score": 0.0,
                "flagged_categories": [],
            }

        # 1. Primary: Run Detoxify Model if loaded
        if self.detoxify_model:
            try:
                model_out = self.detoxify_model.predict(text)
                scores = {
                    "toxicity": float(model_out.get("toxicity", 0.0)),
                    "severe_toxicity": float(model_out.get("severe_toxicity", 0.0)),
                    "insult": float(model_out.get("insult", 0.0)),
                    "threat": float(model_out.get("threat", 0.0)),
                    "identity_attack": float(model_out.get("identity_attack", 0.0)),
                    "sexual_explicit": float(model_out.get("sexual_explicit", 0.0)),
                }
                return self._classify_scores(scores)
            except Exception as ex:
                logger.warning(f"Detoxify inference error: {ex}. Falling back to heuristic evaluator.")

        # 2. Secondary: Fallback Local Heuristic Evaluator
        return self._heuristic_evaluate(text)

    def _heuristic_evaluate(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        scores = {
            "toxicity": 0.0,
            "severe_toxicity": 0.0,
            "insult": 0.0,
            "threat": 0.0,
            "identity_attack": 0.0,
            "sexual_explicit": 0.0,
        }

        for category, patterns in TOXICITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    scores[category] = max(scores[category], 0.75)
                    if category in ["threat", "identity_attack"]:
                        scores["severe_toxicity"] = max(scores["severe_toxicity"], 0.80)
                    scores["toxicity"] = max(scores["toxicity"], 0.70)

        return self._classify_scores(scores)

    def _classify_scores(self, scores: Dict[str, float]) -> Dict[str, Any]:
        max_score = max(scores.values()) if scores else 0.0
        flagged = [cat for cat, val in scores.items() if val >= self.review_threshold]

        if max_score >= self.unsafe_threshold:
            classification = "UNSAFE"
        elif max_score >= self.review_threshold:
            classification = "REVIEW"
        else:
            classification = "SAFE"

        return {
            "scores": {k: round(v, 4) for k, v in scores.items()},
            "classification": classification,
            "max_score": round(max_score, 4),
            "flagged_categories": flagged,
        }
