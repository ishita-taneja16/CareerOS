MEMORY_EXTRACTION_PROMPT = """
Identify if the user is stating a long-term personal preference, experience, certification, or goal in the text.
If yes, summarize it into a concise single statement.
Output ONLY the statement or empty string if no core fact was stated.

User message: "{message}"
"""
