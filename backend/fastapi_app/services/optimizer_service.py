import json
from typing import Dict, Any
# pyrefly: ignore [missing-import]
from litellm import completion
from config import settings
from models.resume_schema import ResumeSchema

class ResumeOptimizerService:
    def optimize(self, resume: ResumeSchema, jd_text: str) -> ResumeSchema:
        """
        Uses an LLM to align skills and experience bullet points with the target Job Description.
        """
        prompt = f"""
You are an expert resume writer. Optimize the structured resume below to align with the target Job Description (JD).
Modify the bullet points in experience and projects to highlight accomplishments relevant to the JD using the STAR method (Situation, Task, Action, Result).
Incorporate missing keywords into the 'skills' list and experience descriptions naturally, but do not invent fake qualifications.
Return the result ONLY as a JSON object matching the exact schema as the input.

Target Job Description:
---
{jd_text}
---

Input Resume JSON:
---
{resume.model_dump_json(indent=2)}
---
"""

        model = "gemini/gemini-1.5-flash" if settings.GEMINI_API_KEY else "ollama/llama3"
        api_key = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY else None

        try:
            response = completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            # Clean markdown wraps
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            optimized_dict = json.loads(content)
            return ResumeSchema(**optimized_dict)
        except Exception:
            # If optimization fails, return original resume unchanged
            return resume
