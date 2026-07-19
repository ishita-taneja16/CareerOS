from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from services.search_service import JobSearchService
from services.ats_service import ATSEngine
from models.resume_schema import ResumeSchema

router = APIRouter()
search_service = JobSearchService()
ats_engine = ATSEngine()

class JobSearchRequest(BaseModel):
    query: str
    location: str = "Remote"
    resume: ResumeSchema

@router.post("/search", status_code=status.HTTP_200_OK)
async def search_and_rank_jobs(request: JobSearchRequest):
    """
    Search job openings using crawler and rank results against candidate's
    active resume using the ATS similarity scores.
    """
    try:
        # 1. Fetch job listings
        jobs = await search_service.search_jobs(request.query, request.location)
        
        ranked_jobs = []
        for job in jobs:
            # 2. Score similarity using ATS Engine
            jd_text = f"{job['role_title']} role description: {job['job_description']}"
            analysis = ats_engine.analyze(request.resume, jd_text)
            
            # Formulate explaining summary
            strengths_summary = analysis["strengths"][0] if analysis["strengths"] else "General match."
            explanation = f"Match score is guided by keyword overlap ({analysis['subscores']['keyword_match']}%). {strengths_summary}"
            
            # Extract matched skills
            jd_keywords = ats_engine.extract_keywords_from_jd(jd_text)
            matched_skills = [kw for kw in jd_keywords if kw not in analysis["missing_keywords"]]
            
            ranked_jobs.append({
                "job_id": job.get("job_id", ""),
                "company": job["company"],
                "role_title": job["role_title"],
                "location": job["location"],
                "job_description": job["job_description"],
                "salary": job["salary"],
                "salary_min": job.get("salary_min", 0),
                "salary_max": job.get("salary_max", 0),
                "salary_currency": job.get("salary_currency", "INR"),
                "source": job["source"],
                "apply_url": job["apply_url"],
                "logo": job.get("logo", ""),
                "posted_date": job.get("posted_date", "2026-07-04"),
                "employment_type": job.get("employment_type", "Full-time"),
                "work_type": job.get("work_type", "Remote"),
                "experience_level": job.get("experience_level", "Mid"),
                "verified": job.get("verified", True),
                "match_percentage": analysis["ats_score"],
                "matched_skills": list(set(matched_skills)),
                "missing_skills": list(set(analysis["missing_keywords"])),
                "explanation": explanation
            })
            
        # 3. Sort by combined ranking score descending (ATS + Recency + Relevance)
        import datetime
        today = datetime.date(2026, 7, 4)
        
        for job in ranked_jobs:
            ats = job["match_percentage"]
            
            # Recency bonus
            recency_bonus = 0
            try:
                posted_dt = datetime.datetime.strptime(job["posted_date"], "%Y-%m-%d").date()
                days_diff = (today - posted_dt).days
                if days_diff <= 0:
                    recency_bonus = 10
                elif days_diff == 1:
                    recency_bonus = 7
                elif days_diff <= 3:
                    recency_bonus = 5
                elif days_diff <= 7:
                    recency_bonus = 2
            except Exception:
                pass
                
            # Query relevance bonus
            relevance_bonus = 0
            q_clean = request.query.lower().strip()
            if q_clean:
                title_lower = job["role_title"].lower()
                desc_lower = job["job_description"].lower()
                if q_clean in title_lower:
                    relevance_bonus = 15
                elif q_clean in desc_lower:
                    relevance_bonus = 5
                    
            job["combined_rank_score"] = ats + recency_bonus + relevance_bonus
            
        ranked_jobs.sort(key=lambda x: x["combined_rank_score"], reverse=True)
        return {"results": ranked_jobs}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job search ranking failed: {str(e)}"
        )
