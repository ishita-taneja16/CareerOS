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
            
            ranked_jobs.append({
                "company": job["company"],
                "role_title": job["role_title"],
                "location": job["location"],
                "job_description": job["job_description"],
                "salary": job["salary"],
                "source": job["source"],
                "match_percentage": analysis["ats_score"],
                "explanation": explanation
            })
            
        # 3. Sort by match score descending
        ranked_jobs.sort(key=lambda x: x["match_percentage"], reverse=True)
        return {"results": ranked_jobs}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job search ranking failed: {str(e)}"
        )
