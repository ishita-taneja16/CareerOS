import re
from typing import List, Dict, Any, Tuple
# pyrefly: ignore [missing-import]
import spacy
# pyrefly: ignore [missing-import]
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models.resume_schema import ResumeSchema

# Standard lists for heuristics
STRONG_ACTION_VERBS = {
    "led", "managed", "spearheaded", "designed", "developed", "built", "implemented",
    "created", "optimized", "improved", "increased", "decreased", "engineered",
    "architected", "formulated", "established", "orchestrated", "supervised",
    "coordinated", "executed", "accelerated", "maximized", "minimized", "produced"
}

COMMON_STOPWORDS = {
    "and", "the", "for", "with", "this", "that", "from", "these", "those", "their",
    "work", "project", "experience", "role", "team", "responsibilities", "system"
}

class ATSEngine:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            self.nlp = None

    def extract_keywords_from_jd(self, jd_text: str) -> List[str]:
        """Extracts technical nouns and proper nouns from job description."""
        if not self.nlp:
            # Fallback regex extraction of words starting with uppercase or general alphabetic words
            words = re.findall(r'\b[a-zA-Z]{3,15}\b', jd_text)
            return list(set([w.lower() for w in words if w.lower() not in COMMON_STOPWORDS]))

        doc = self.nlp(jd_text)
        keywords = []
        for token in doc:
            # Look for nouns, proper nouns, and foreign words (often technology acronyms)
            if token.pos_ in ["NOUN", "PROPN", "X"] and not token.is_stop:
                word = token.text.strip().lower()
                if len(word) > 2 and word not in COMMON_STOPWORDS:
                    keywords.append(word)
        return list(set(keywords))

    def calculate_keyword_score(self, resume_keywords: List[str], jd_keywords: List[str]) -> Tuple[float, List[str]]:
        """Calculates fuzzy matching overlap ratio between resume terms and JD requirements."""
        if not jd_keywords:
            return 100.0, []

        matched = []
        missing = []
        
        for jd_kw in jd_keywords:
            match_found = False
            for res_kw in resume_keywords:
                # Direct match or high fuzzy similarity
                if jd_kw == res_kw or fuzz.ratio(jd_kw, res_kw) > 85:
                    matched.append(jd_kw)
                    match_found = True
                    break
            if not match_found:
                missing.append(jd_kw)

        score = (len(matched) / len(jd_keywords)) * 100.0
        return round(score, 2), missing

    def calculate_action_verb_score(self, experience_bullets: List[str]) -> Tuple[float, List[str]]:
        """Verifies if experience bullet points start with strong action verbs."""
        if not experience_bullets:
            return 0.0, ["Resume does not have any experience bullet points."]

        compliant_count = 0
        suggestions = []

        for bullet in experience_bullets:
            bullet_clean = bullet.strip().lstrip("-*• ").strip()
            if not bullet_clean:
                continue

            words = bullet_clean.split()
            first_word = words[0].lower() if words else ""
            # Strip non-alphanumeric chars
            first_word = re.sub(r'[^a-z]', '', first_word)

            if first_word in STRONG_ACTION_VERBS:
                compliant_count += 1
            else:
                # Fallback: check if spaCy tags it as a verb
                if self.nlp:
                    doc = self.nlp(words[0] if words else "")
                    if doc and doc[0].pos_ == "VERB":
                        compliant_count += 1
                        continue
                
                suggestions.append(f"Consider rewriting: '{bullet_clean[:60]}...' with a strong action verb (e.g., 'Spearheaded', 'Optimized').")

        score = (compliant_count / len(experience_bullets)) * 100.0
        return round(score, 2), suggestions

    def calculate_semantic_score(self, resume_text: str, jd_text: str) -> float:
        """Calculates cosine similarity of TF-IDF vectors for global context alignment."""
        if not resume_text or not jd_text:
            return 0.0
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf = vectorizer.fit_transform([resume_text, jd_text])
            similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])
            return round(float(similarity[0][0]) * 100.0, 2)
        except Exception:
            return 50.0 # Standard fallback

    def calculate_formatting_score(self, resume: ResumeSchema) -> Tuple[float, List[str]]:
        """Evaluates resume completeness and contact detail accessibility."""
        score = 100.0
        warnings = []

        if not resume.contact_info.email:
            score -= 20
            warnings.append("Missing email address.")
        if not resume.contact_info.phone:
            score -= 10
            warnings.append("Missing phone number.")
        if not resume.skills:
            score -= 20
            warnings.append("Missing skills section.")
        if not resume.experiences:
            score -= 25
            warnings.append("Missing professional experience history.")
        if not resume.education:
            score -= 15
            warnings.append("Missing education history.")
        if not resume.projects:
            score -= 10
            warnings.append("Missing projects section.")

        return max(score, 0.0), warnings

    def analyze(self, resume: ResumeSchema, jd_text: str) -> Dict[str, Any]:
        """Orchestrates standard scoring formulas and generates diagnostic insights."""
        # 1. Extract all text from resume for semantic calculations
        resume_parts = []
        resume_keywords = []

        # Skills
        resume_parts.extend(resume.skills)
        resume_keywords.extend([s.lower() for s in resume.skills])

        # Experience
        exp_bullets = []
        for exp in resume.experiences:
            exp_text = f"{exp.role} at {exp.company} {exp.location}. " + " ".join(exp.description_bullets)
            resume_parts.append(exp_text)
            exp_bullets.extend(exp.description_bullets)
            resume_keywords.extend([t.lower() for t in exp.technologies])
            # Parse tokens in company/role as keywords
            resume_keywords.extend(re.findall(r'\b\w{3,15}\b', exp.role.lower()))
            resume_keywords.extend(re.findall(r'\b\w{3,15}\b', exp.company.lower()))

        # Projects
        proj_bullets = []
        for proj in resume.projects:
            proj_text = f"{proj.name}: " + " ".join(proj.description_bullets)
            resume_parts.append(proj_text)
            proj_bullets.extend(proj.description_bullets)
            resume_keywords.extend([t.lower() for t in proj.technologies])
            resume_keywords.extend(re.findall(r'\b\w{3,15}\b', proj.name.lower()))

        # Education
        for edu in resume.education:
            edu_text = f"{edu.degree} in {edu.field_of_study} from {edu.institution}."
            resume_parts.append(edu_text)

        global_resume_text = " ".join(resume_parts)
        resume_keywords = list(set(resume_keywords))

        # 2. Run Individual Audits
        jd_keywords = self.extract_keywords_from_jd(jd_text)
        keyword_score, missing_kws = self.calculate_keyword_score(resume_keywords, jd_keywords)
        action_verb_score, verb_warnings = self.calculate_action_verb_score(exp_bullets)
        semantic_score = self.calculate_semantic_score(global_resume_text, jd_text)
        formatting_score, formatting_warnings = self.calculate_formatting_score(resume)

        # Experience year matches logic (heuristic)
        # Parse years from JD
        jd_years_match = re.search(r'(\d+)\+?\s*years?', jd_text, re.IGNORECASE)
        required_years = int(jd_years_match.group(1)) if jd_years_match else 0
        
        # Calculate resume years
        # Very simple estimator (sum of month differences, default to 1 year per role if start/end unparseable)
        parsed_years = len(resume.experiences) * 1.5 
        exp_match_score = 100.0 if parsed_years >= required_years else (parsed_years / max(required_years, 1)) * 100.0
        exp_match_score = round(min(exp_match_score, 100.0), 2)

        # 3. Overall Weighted Score
        # W_kw: 0.30, W_sem: 0.30, W_act: 0.15, W_fmt: 0.15, W_exp: 0.10
        ats_score = (
            0.30 * keyword_score +
            0.30 * semantic_score +
            0.15 * action_verb_score +
            0.15 * formatting_score +
            0.10 * exp_match_score
        )
        ats_score = round(ats_score, 2)

        # 4. Compile Strengths & Weaknesses
        strengths = []
        weaknesses = []
        priority_suggestions = []

        if keyword_score >= 80:
            strengths.append(f"Excellent keyword overlap ({keyword_score}%). Your resume contains key vocabulary from the job description.")
        else:
            weaknesses.append(f"Low keyword matching overlap ({keyword_score}%). Important technical tools are missing.")
            priority_suggestions.append("Incorporate missing keywords like: " + ", ".join(missing_kws[:6]))

        if action_verb_score >= 75:
            strengths.append(f"Strong action verb presence ({action_verb_score}%). Your bullet points show active impact.")
        else:
            weaknesses.append(f"Weak action verb utilization ({action_verb_score}%). Multiple bullet points start with passive phrases.")
            priority_suggestions.extend(verb_warnings[:2])

        if semantic_score >= 70:
            strengths.append("High context similarity. The description of your projects aligns well with the roles requested.")
        else:
            weaknesses.append("Moderate content alignment. The terminology in your experience details differs from the job profile context.")
            priority_suggestions.append("Rewrite project summaries to emphasize deliverables and architectures matching the job requirements.")

        if formatting_score == 100:
            strengths.append("Standard format layout. All crucial sections (contact, skills, experience, education) are present.")
        else:
            weaknesses.extend(formatting_warnings)
            priority_suggestions.append("Add the missing structural fields to meet standard recruiting parsers.")

        return {
            "ats_score": ats_score,
            "subscores": {
                "keyword_match": keyword_score,
                "semantic_similarity": semantic_score,
                "action_verbs": action_verb_score,
                "formatting_score": formatting_score,
                "experience_match": exp_match_score
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_keywords": missing_kws,
            "priority_suggestions": priority_suggestions
        }
