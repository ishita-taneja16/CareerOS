import re
import logging
from typing import Dict, Any, Optional, List
from .bias_detector import BiasDetector
from .toxicity_evaluator import ToxicityEvaluator
from .groundedness_evaluator import GroundednessEvaluator

logger = logging.getLogger(__name__)

UNSAFE_PROMPT_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"bypass\s+safety\s+filter",
    r"reveal\s+system\s+prompt",
]


class ResponsibleAIGuardrailManager:
    """
    Central Manager for Responsible AI in CareerOS.
    Executes input prompt validation, bias detection, toxicity checks,
    groundedness audits, and output safety filters across all LLM operations.
    """

    def __init__(self, enable_guardrails: bool = True, bias_threshold: float = 0.15):
        self.enable_guardrails = enable_guardrails
        self.bias_detector = BiasDetector(threshold=bias_threshold)
        self.toxicity_evaluator = ToxicityEvaluator(review_threshold=0.30, unsafe_threshold=0.60)
        self.groundedness_evaluator = GroundednessEvaluator()

    def validate_input(self, prompt: str) -> Dict[str, Any]:
        """
        Validates user prompts for prompt injection, unsafe directives, or malicious patterns.
        """
        if not self.enable_guardrails or not prompt:
            return {"is_valid": True, "reason": None}

        prompt_lower = prompt.lower()
        for pattern in UNSAFE_PROMPT_PATTERNS:
            if re.search(pattern, prompt_lower):
                logger.warning(f"Unsafe prompt injection pattern detected: {pattern}")
                return {
                    "is_valid": False,
                    "reason": "Input contains disallowed system override instructions.",
                }

        return {"is_valid": True, "reason": None}

    def validate_output(
        self, output_text: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Scans model output for demographic bias, toxicity violations, and factual groundedness.
        """
        if not self.enable_guardrails or not output_text:
            return {
                "is_safe": True,
                "output_text": output_text,
                "bias_analysis": {"has_bias": False, "bias_score": 0.0},
                "toxicity_analysis": {"classification": "SAFE"},
                "groundedness_analysis": {"grounded": True, "hallucination_risk": "low"},
                "warnings": [],
            }

        context = context or {}

        # 1. Bias Analysis
        bias_res = self.bias_detector.analyze_text(output_text)

        # 2. Toxicity Evaluation
        toxicity_res = self.toxicity_evaluator.evaluate_text(output_text)

        # 3. Groundedness Evaluation
        groundedness_res = self.groundedness_evaluator.evaluate_groundedness(
            response_text=output_text,
            structured_resume_data=context.get("structured_resume_data"),
            job_description=context.get("job_description"),
            retrieved_context=context.get("retrieved_context")
        )

        # Construct Audit Response
        warnings: List[str] = list(bias_res.get("warnings", []))
        if toxicity_res.get("classification") != "SAFE":
            warnings.append(f"Toxicity Warning: Output classified as {toxicity_res.get('classification')}")
        if not groundedness_res.get("grounded"):
            warnings.append(f"Groundedness Warning: Risk level {groundedness_res.get('hallucination_risk')}")

        is_safe = (
            not bias_res.get("has_bias", False)
            and toxicity_res.get("classification") != "UNSAFE"
            and groundedness_res.get("grounded", True)
        )

        return {
            "is_safe": is_safe,
            "output_text": output_text,
            "bias_analysis": bias_res,
            "toxicity_analysis": toxicity_res,
            "groundedness_analysis": groundedness_res,
            "warnings": warnings,
        }
