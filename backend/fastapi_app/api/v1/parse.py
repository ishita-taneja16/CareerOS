import os
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from services.parser_service import ParserService
from models.resume_schema import ResumeSchema

router = APIRouter()
parser_service = ParserService()

@router.post("/", response_model=ResumeSchema, status_code=status.HTTP_200_OK)
async def parse_resume(file: UploadFile = File(...)):
    """
    Upload a resume file (PDF or DOCX) to extract structured JSON data.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file extension. Only .pdf, .docx, and .doc are supported."
        )

    # Save to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:
        # Run parsing pipeline
        structured_resume = parser_service.parse(temp_path)
        return structured_resume
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during resume parsing: {str(e)}"
        )
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
