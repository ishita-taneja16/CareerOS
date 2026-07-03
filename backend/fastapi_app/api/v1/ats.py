from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from models.resume_schema import ResumeSchema
from services.ats_service import ATSEngine
from services.optimizer_service import ResumeOptimizerService

router = APIRouter()
ats_engine = ATSEngine()
optimizer_service = ResumeOptimizerService()

class ATSRequest(BaseModel):
    resume: ResumeSchema
    job_description: str

@router.post("/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_resume(request: ATSRequest):
    """
    Evaluate a structured resume against a target job description and return granular subscores,
    strengths, weaknesses, missing keywords, and suggestions.
    """
    try:
        results = ats_engine.analyze(request.resume, request.job_description)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ATS evaluation failed: {str(e)}"
        )

@router.post("/optimize", response_model=ResumeSchema, status_code=status.HTTP_200_OK)
async def optimize_resume(request: ATSRequest):
    """
    Optimize a structured resume to match a target job description, rewriting points and
    injecting keywords where appropriate.
    """
    try:
        optimized_resume = optimizer_service.optimize(request.resume, request.job_description)
        return optimized_resume
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume optimization failed: {str(e)}"
        )
