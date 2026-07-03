RESUME_OPTIMIZATION_PROMPT = """
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
{resume_json}
---
"""
