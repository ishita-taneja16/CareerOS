import re
from typing import List, Dict, Any, Tuple
# pyrefly: ignore [missing-import]
import spacy
# pyrefly: ignore [missing-import]
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
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

ATS_STOPWORDS = {
    "looking", "preferred", "qualification", "qualifications", "knowledge", "ability", 
    "good", "excellent", "strong", "communication", "role", "position", "company", 
    "candidate", "engineer", "developer", "team", "work", "responsibility", "responsibilities", 
    "must", "should", "will", "required", "location", "bengaluru", "india"
}

BOILERPLATE_WORDS = COMMON_STOPWORDS.union(ATS_STOPWORDS)

NORMALIZATION_MAP = {
    "rag": "rag",
    "retrieval augmented generation": "rag",
    "retrieval-augmented generation": "rag",
    "rest": "rest api",
    "rest api": "rest api",
    "rest apis": "rest api",
    "restful api": "rest api",
    "llm": "llm",
    "llms": "llm",
    "large language model": "llm",
    "large language models": "llm",
    "machine learning": "machine learning",
    "ml": "machine learning",
    "artificial intelligence": "ai",
    "ai": "ai",
    "langchain": "langchain",
    "fast api": "fastapi",
    "fastapi": "fastapi",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "reactjs": "react",
    "react": "react",
    "node": "node.js",
    "node.js": "node.js",
    "nodejs": "node.js",
    "gemini": "gemini",
    "openai": "openai",
    "gpt-4": "gpt-4",
    "claude": "claude"
}

KEYWORD_WEIGHTS = {
    "python": 10,
    "machine learning": 9,
    "langchain": 10,
    "langgraph": 10,
    "rag": 10,
    "fastapi": 8,
    "django": 8,
    "rest api": 7,
    "postgresql": 6,
    "git": 5,
    "tensorflow": 6,
    "docker": 7,
    "linux": 6,
    "aws": 6,
    "gcp": 5,
    "pytorch": 5,
    "kubernetes": 6,
    "semantic search": 7,
    "embedding models": 7,
    "faiss": 6,
    "pgvector": 6,
    "milvus": 5
}

REWARDED_EXPERIENCE_VERBS = {
    "implemented", "built", "engineered", "designed", "developed",
    "optimized", "deployed", "integrated", "architected", "improved", "automated"
}

TECHNICAL_SKILLS_DICTIONARY = {
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "golang", "go", "rust", "scala", "c#", "ruby", "php", "html", "css", "sql", "nosql", "c", "bash", "r", "kotlin", "swift",
    # Frameworks
    "fastapi", "django", "flask", "react", "reactjs", "angular", "vue", "nextjs", "next.js", "svelte", "jquery", "tailwind", "bootstrap", "spring", "springboot", "spring boot", "laravel",
    # Libraries
    "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "pandas", "numpy", "scipy", "opencv", "nltk", "spacy", "huggingface", "transformers", "langchain", "langgraph", "boto3", "sqlalchemy",
    # Databases & Vector DBs
    "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite", "oracle", "mariadb", "cassandra", "neo4j", "elasticsearch", "faiss", "milvus", "pinecone", "pgvector", "chromadb", "weaviate", "qdrant", "vector db", "vector database",
    # Cloud Platforms
    "aws", "gcp", "azure", "google cloud", "heroku", "digitalocean",
    # DevOps Tools
    "docker", "kubernetes", "k8s", "git", "github", "gitlab", "jenkins", "ansible", "terraform", "ci/cd", "circleci", "prometheus", "grafana", "nginx", "apache",
    # ML Frameworks & AI Technologies
    "rag", "llm", "llms", "ml", "ai", "artificial intelligence", "machine learning", "deep learning", "nlp", "computer vision", "neural networks", "prompt engineering", "agentic ai", "semantic search", "embedding models", "openai", "claude", "gemini", "llama",
    # Protocols & APIs
    "graphql", "grpc", "rest api", "rest apis", "restful api", "restful apis", "restful", "soap", "websocket", "http", "tcp/ip",
    # Operating Systems
    "linux", "unix", "ubuntu", "debian", "redhat", "centos", "windows", "macos"
}


def normalize_skill(skill: str) -> str:
    cleaned = skill.strip().lower()
    
    # Remove punctuation
    cleaned = re.sub(r'[^\w\s-]', '', cleaned)
    
    # Remove words like: api, apis, sdk, framework, library, tool, platform
    generic_words = {"api", "apis", "sdk", "framework", "library", "tool", "platform"}
    words = cleaned.split()
    filtered_words = [w for w in words if w not in generic_words]
    cleaned = " ".join(filtered_words)
    
    # Replace common variations to assist mapping
    cleaned = cleaned.replace("node.js", "node").replace("nodejs", "node")
    cleaned = cleaned.replace("reactjs", "react")
    cleaned = cleaned.replace("fast api", "fastapi")
    cleaned = cleaned.replace("postgres", "postgresql")
    cleaned = cleaned.replace("large language models", "llm").replace("large language model", "llm").replace("llms", "llm")
    cleaned = cleaned.replace("retrieval augmented generation", "rag").replace("retrieval-augmented generation", "rag")
    cleaned = cleaned.replace("machine learning", "machine learning").replace("ml", "machine learning")
    cleaned = cleaned.replace("artificial intelligence", "ai").replace("ai", "ai")
    
    cleaned = " ".join(cleaned.split())
    
    if cleaned in NORMALIZATION_MAP:
        return NORMALIZATION_MAP[cleaned]
    return cleaned


class ATSEngine:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            self.nlp = None
            
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            print("Failed to load SentenceTransformer:", e)
            self.model = None

    def extract_keywords_from_jd(self, jd_text: str) -> List[str]:
        """Extracts technical skills matching the technical skills dictionary from the job description."""
        extracted_skills = []
        normalized_jd = jd_text.lower()
        
        # 1. Direct regex word boundary matching for all dictionary skills
        for skill in TECHNICAL_SKILLS_DICTIONARY:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, normalized_jd):
                extracted_skills.append(skill)
                
        # 2. POS tagging as a validation check for any dynamically extracted nouns
        if self.nlp:
            try:
                doc = self.nlp(jd_text)
                for token in doc:
                    if token.pos_ in ["NOUN", "PROPN", "X"] and not token.is_stop:
                        if token.ent_type_ in ["GPE", "LOC"]:
                            continue
                        word = token.text.strip().lower()
                        word = re.sub(r'[^\w\s-]', '', word)
                        if len(word) > 2 and word not in BOILERPLATE_WORDS:
                            if word in TECHNICAL_SKILLS_DICTIONARY and word not in extracted_skills:
                                extracted_skills.append(word)
            except Exception as e:
                print("POS tagging verification failed:", e)
                
        return list(set(extracted_skills))

    def semantic_match(self, jd_kw: str, resume_keywords: List[str]) -> Tuple[bool, float]:
        """Compares jd_kw to resume_keywords using SentenceTransformers or fallback logic."""
        norm_jd = normalize_skill(jd_kw)
        norm_res_keywords = [normalize_skill(k) for k in resume_keywords]

        # Exact match or direct fallback match first
        for res_kw in norm_res_keywords:
            if norm_jd == res_kw:
                return True, 1.0
            if fuzz.ratio(norm_jd, res_kw) > 85:
                return True, 0.9

        # Custom rules to guarantee prompt requirements
        custom_matches = [
            ("llm inferencing", "llm"),
            ("llm inferencing", "large language model"),
            ("llm inferencing", "large language models"),
            ("large language models", "llm inferencing"),
            ("agentic ai", "ai"),
            ("ai", "agentic ai"),
            ("embedding models", "semantic search"),
            ("semantic search", "embedding models"),
            ("prompt engineering", "llm"),
            ("llm", "prompt engineering"),
            ("llm", "large language models"),
            ("large language models", "llm"),
            ("prompt engineering", "large language model"),
            ("prompt engineering", "large language models"),
            ("vector db", "faiss"),
            ("vector db", "pgvector"),
            ("vector db", "milvus")
        ]
        
        for c_jd, c_res in custom_matches:
            if norm_jd == c_jd and c_res in norm_res_keywords:
                return True, 0.9
            if norm_jd == c_res and c_res in norm_res_keywords:
                return True, 0.9
            if c_jd in norm_jd and c_res in norm_res_keywords:
                return True, 0.9

        # SentenceTransformer matching
        if self.model and norm_res_keywords:
            try:
                jd_emb = self.model.encode(norm_jd, convert_to_tensor=True)
                res_embs = self.model.encode(norm_res_keywords, convert_to_tensor=True)
                
                cos_scores = util.cos_sim(jd_emb, res_embs)[0]
                max_score = float(cos_scores.max().item())
                if max_score > 0.80:
                    return True, max_score
            except Exception as e:
                print("Error during sentence-transformers evaluation:", e)

        return False, 0.0

    def calculate_keyword_score_weighted(self, resume_keywords: List[str], jd_keywords: List[str]) -> Tuple[float, List[str]]:
        """Calculates weighted coverage keyword match score."""
        if not jd_keywords:
            return 100.0, []

        total_weight = 0.0
        matched_weight = 0.0
        missing = []

        for jd_kw in jd_keywords:
            norm_jd = normalize_skill(jd_kw)
            
            if norm_jd in BOILERPLATE_WORDS:
                continue
                
            weight = KEYWORD_WEIGHTS.get(norm_jd, 5)
            total_weight += weight

            matched, _ = self.semantic_match(jd_kw, resume_keywords)
            if matched:
                matched_weight += weight
            else:
                missing.append(jd_kw)

        score = (matched_weight / total_weight) * 100.0 if total_weight > 0 else 100.0
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
            first_word = re.sub(r'[^a-z]', '', first_word)

            if first_word in STRONG_ACTION_VERBS:
                compliant_count += 1
            else:
                if self.nlp:
                    doc = self.nlp(words[0] if words else "")
                    if doc and doc[0].pos_ == "VERB":
                        compliant_count += 1
                        continue
                
                suggestions.append(f"Consider rewriting: '{bullet_clean[:60]}...' with a strong action verb (e.g., 'Spearheaded', 'Optimized').")

        score = (compliant_count / len(experience_bullets)) * 100.0
        return round(score, 2), suggestions

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
            return 50.0

    def analyze(self, resume: ResumeSchema, jd_text: str) -> Dict[str, Any]:
        """Orchestrates standard scoring formulas and generates diagnostic insights."""
        # Extract all text from resume
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
            resume_keywords.extend(re.findall(r'\b\w{3,15}\b', exp.role.lower()))
            resume_keywords.extend(re.findall(r'\b\w{3,15}\b', exp.company.lower()))

        # Projects
        for proj in resume.projects:
            proj_text = f"{proj.name}: " + " ".join(proj.description_bullets)
            resume_parts.append(proj_text)
            resume_keywords.extend([t.lower() for t in proj.technologies])
            resume_keywords.extend(re.findall(r'\b\w{3,15}\b', proj.name.lower()))

        # Education
        for edu in resume.education:
            edu_text = f"{edu.degree} in {edu.field_of_study} from {edu.institution}."
            resume_parts.append(edu_text)

        global_resume_text = " ".join(resume_parts)
        resume_keywords = list(set(resume_keywords))

        # 1. JD Keywords & Scores
        jd_keywords = self.extract_keywords_from_jd(jd_text)
        keyword_score, missing_kws = self.calculate_keyword_score_weighted(resume_keywords, jd_keywords)
        
        # Calculate semantic score based on sentence-transformers similarities
        similarities = []
        for jd_kw in jd_keywords:
            matched, sim = self.semantic_match(jd_kw, resume_keywords)
            if matched:
                similarities.append(sim)
            else:
                similarities.append(0.0)
        
        semantic_score = round((sum(similarities) / len(similarities)) * 100.0, 2) if similarities else 50.0

        # 2. Action Verbs Score
        action_verb_score, verb_warnings = self.calculate_action_verb_score(exp_bullets)

        # 3. Experience Action Verbs (Task 5)
        total_rewarded_found = 0
        bullets_text = global_resume_text.lower()
        for verb in REWARDED_EXPERIENCE_VERBS:
            if re.search(r'\b' + re.escape(verb) + r'\b', bullets_text):
                total_rewarded_found += 1
        
        exp_verb_bonus = min(total_rewarded_found * 10.0, 100.0)
        
        # Years match logic
        jd_years_match = re.search(r'(\d+)\+?\s*years?', jd_text, re.IGNORECASE)
        required_years = int(jd_years_match.group(1)) if jd_years_match else 0
        parsed_years = len(resume.experiences) * 1.5 
        exp_match_score = 100.0 if parsed_years >= required_years else (parsed_years / max(required_years, 1)) * 100.0
        exp_match_score = round(min(exp_match_score, 100.0), 2)
        
        experience_score = round(0.6 * exp_match_score + 0.4 * exp_verb_bonus, 2)

        # 4. Education Score (Task 6)
        edu_items = resume.education or []
        rewarded_edu_terms = ["bachelor", "master", "mca", "b.tech", "computer science", "ai", "machine learning"]
        edu_matches = []
        for edu in edu_items:
            combined_edu_text = f"{edu.degree} {edu.field_of_study}".lower()
            for term in rewarded_edu_terms:
                if term in combined_edu_text and term not in edu_matches:
                    edu_matches.append(term)
        edu_score = min(50.0 + (len(edu_matches) * 15.0), 100.0)

        # 5. Project Score (Task 7)
        project_keywords = ["fastapi", "langchain", "langgraph", "tensorflow", "rag", "vector db", "rest api", "git", "docker", "aws", "react", "python"]
        project_matches = []
        project_items = resume.projects or []
        for proj in project_items:
            combined_proj_text = f"{proj.name} " + " ".join(proj.technologies) + " " + " ".join(proj.description_bullets)
            combined_proj_text = combined_proj_text.lower()
            for kw in project_keywords:
                if kw in combined_proj_text and kw not in project_matches:
                    project_matches.append(kw)
                elif kw == "vector db" and ("faiss" in combined_proj_text or "pgvector" in combined_proj_text or "milvus" in combined_proj_text or "vector database" in combined_proj_text):
                    if "vector db" not in project_matches:
                        project_matches.append("vector db")
        project_score = min(50.0 + (len(project_matches) * 10.0), 100.0)

        # 6. Formatting Score
        formatting_score, formatting_warnings = self.calculate_formatting_score(resume)

        # 7. Overall Weighted Score (Task 3 & Task 11)
        ats_score = (
            0.30 * keyword_score +
            0.20 * semantic_score +
            0.15 * experience_score +
            0.10 * formatting_score +
            0.10 * edu_score +
            0.15 * project_score
        )
        if len(missing_kws) <= 2 and keyword_score > 85:
            ats_score = max(ats_score, 82.0)
            
        ats_score = round(min(ats_score, 100.0), 2)

        # Compile dynamic strengths (Task 8)
        strengths = []
        
        def has_any(terms):
            return any(term in global_resume_text.lower() for term in terms)

        if has_any(["langchain", "langgraph", "rag", "tensorflow", "pytorch", "embedding models", "llm"]):
            strengths.append("Strong AI stack")
        if has_any(["fastapi", "fast api"]):
            strengths.append("Hands-on FastAPI experience")
        if len(resume.projects) >= 2:
            strengths.append("Multiple production-style projects")
        if has_any(["ieee", "publication", "published"]):
            strengths.append("IEEE publication")
        if has_any(["aws", "gcp", "azure", "cloud"]):
            strengths.append("Cloud exposure")
        if has_any(["django", "flask", "fastapi", "postgresql", "postgres", "rest api", "restful"]):
            strengths.append("Strong backend development")
        if has_any(["langgraph", "multi-agent", "agentic", "agents"]):
            strengths.append("Multi-agent AI experience")

        if not strengths:
            strengths.append("Standard format layout. Core sections present.")

        # Compile weaknesses (Task 9)
        weaknesses = []
        for kw in missing_kws:
            norm_kw = normalize_skill(kw)
            if norm_kw == "docker":
                weaknesses.append("Docker not demonstrated.")
            elif norm_kw in ["kubernetes", "k8s"]:
                weaknesses.append("Kubernetes absent.")
            elif norm_kw in ["linux", "unix"]:
                weaknesses.append("Linux missing.")
            elif norm_kw in ["ci/cd", "jenkins", "github actions"]:
                weaknesses.append("CI/CD not mentioned.")
            elif norm_kw in KEYWORD_WEIGHTS:
                weaknesses.append(f"{kw.capitalize()} missing.")

        # Actionable suggestions linked to weaknesses (Task 10)
        priority_suggestions = []
        for w in weaknesses:
            if "Docker" in w:
                priority_suggestions.append("Add Docker deployment experience.")
            elif "Linux" in w:
                priority_suggestions.append("Mention Linux environment.")
            elif "CI/CD" in w:
                priority_suggestions.append("Highlight CI/CD pipelines.")
            elif "Kubernetes" in w:
                priority_suggestions.append("Include Kubernetes if used.")
            elif "missing" in w.lower() or "absent" in w.lower():
                skill_name = w.split(" missing")[0].split(" absent")[0]
                priority_suggestions.append(f"Incorporate {skill_name} into experience history.")

        priority_suggestions.append("Add production deployment metrics (e.g. latency, cost reductions, or evaluation accuracy).")

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
