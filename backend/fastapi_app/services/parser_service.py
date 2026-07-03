import os
import re
# pyrefly: ignore [missing-import]
import spacy
from typing import Optional, Dict, Any
# pyrefly: ignore [missing-import]
import fitz  # PyMuPDF
# pyrefly: ignore [missing-import]
from docx import Document
from models.resume_schema import ResumeSchema, ContactInfo
from config import settings
from services.llm_service import LLMService


class ParserService:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            # Fallback if model not downloaded
            self.nlp = None

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extracts text from PDF using PyMuPDF."""
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extracts text from DOCX using python-docx."""
        doc = Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        
        # Read tables too
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text for cell in row.cells]
                text.append(" | ".join(row_text))
                
        return "\n".join(text)

    def extract_text(self, file_path: str) -> str:
        """Determines format and extracts raw text."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def run_llm_parser(self, raw_text: str) -> Dict[str, Any]:
        """Calls LLMService to structure the raw text into JSON."""
        from prompts.resume_prompt import RESUME_PARSER_PROMPT
        prompt = RESUME_PARSER_PROMPT.format(raw_text=raw_text)

        try:
            content = LLMService.call(
                prompt=prompt,
                response_format={"type": "json_object"}
            )
            # Clean possible markdown wrap
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            return json.loads(content)
        except Exception:
            # Return basic metadata if LLM call fails
            return self.run_fallback_parser(raw_text)

    def run_fallback_parser(self, raw_text: str) -> Dict[str, Any]:
        """Simple rule-based parser in case the LLM is offline or fails."""
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        email_match = re.search(email_pattern, raw_text)
        phone_match = re.search(phone_pattern, raw_text)
        
        email = email_match.group(0) if email_match else ""
        phone = phone_match.group(0) if phone_match else ""
        
        name = ""
        if self.nlp:
            doc = self.nlp(raw_text[:200]) # Scan beginning for name
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text
                    break
        
        # If spaCy couldn't find it, take first line
        if not name:
            lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
            name = lines[0] if lines else "Candidate Name"
            
        return {
            "contact_info": {
                "name": name,
                "email": email,
                "phone": phone,
                "location": "",
                "website": None,
                "linkedin": None,
                "github": None
            },
            "skills": [],
            "experiences": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": []
        }

    def parse(self, file_path: str) -> ResumeSchema:
        """Orchestrates document extraction and schema loading."""
        raw_text = self.extract_text(file_path)
        structured_dict = self.run_llm_parser(raw_text)
        return ResumeSchema(**structured_dict)
