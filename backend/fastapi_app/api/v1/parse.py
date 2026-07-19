import os
import shutil
import tempfile
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from services.parser_service import ParserService
from models.resume_schema import ResumeSchema

router = APIRouter()
parser_service = ParserService()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
PARSED_DIR = os.path.join(DATA_DIR, "parsed")
METADATA_FILE = os.path.join(DATA_DIR, "library.json")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(PARSED_DIR, exist_ok=True)

def load_metadata() -> Dict[str, Any]:
    if not os.path.exists(METADATA_FILE):
        return {}
    try:
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_metadata(metadata: Dict[str, Any]):
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=4)

class RenameRequest(BaseModel):
    new_name: str

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

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:
        structured_resume = parser_service.parse(temp_path)
        return structured_resume
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during resume parsing: {str(e)}"
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/library", status_code=status.HTTP_200_OK)
async def get_library_resumes():
    """
    Get a list of all permanently stored resumes in the library.
    """
    metadata = load_metadata()
    return list(metadata.values())

@router.post("/upload", response_model=ResumeSchema, status_code=status.HTTP_200_OK)
async def upload_and_parse_resume(file: UploadFile = File(...)):
    """
    Upload a brand-new resume, save it permanently, parse it, store parsed JSON separately, and return it.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file extension. Only .pdf, .docx, and .doc are supported."
        )

    resume_id = f"resume_{uuid.uuid4().hex[:12]}"
    filename = file.filename
    file_path = os.path.join(UPLOADS_DIR, f"{resume_id}{ext}")
    json_path = os.path.join(PARSED_DIR, f"{resume_id}.json")

    # Write file permanently
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Run parsing pipeline
        structured_resume = parser_service.parse(file_path)
        
        # Save parsed JSON separately
        data_to_save = structured_resume if isinstance(structured_resume, dict) else structured_resume.dict()
        with open(json_path, "w") as f:
            json.dump(data_to_save, f, indent=4)
        
        # Update metadata
        metadata = load_metadata()
        metadata[resume_id] = {
            "id": resume_id,
            "filename": filename,
            "file_path": file_path,
            "json_path": json_path,
            "upload_date": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "parsed": True,
            "file_type": ext.replace(".", "")
        }
        save_metadata(metadata)
        
        return structured_resume
    except Exception as e:
        # Save metadata with parsed = False in case parsing fails
        metadata = load_metadata()
        metadata[resume_id] = {
            "id": resume_id,
            "filename": filename,
            "file_path": file_path,
            "json_path": json_path,
            "upload_date": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "parsed": False,
            "file_type": ext.replace(".", "")
        }
        save_metadata(metadata)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during resume parsing: {str(e)}"
        )

@router.post("/library/{resume_id}/parse", response_model=ResumeSchema, status_code=status.HTTP_200_OK)
async def parse_existing_resume(resume_id: str):
    """
    Parse (or re-parse) an existing stored resume file.
    """
    metadata = load_metadata()
    if resume_id not in metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found in library.")

    record = metadata[resume_id]
    file_path = record["file_path"]
    json_path = record["json_path"]

    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file missing on disk.")

    try:
        structured_resume = parser_service.parse(file_path)
        
        # Save parsed JSON separately
        data_to_save = structured_resume if isinstance(structured_resume, dict) else structured_resume.dict()
        with open(json_path, "w") as f:
            json.dump(data_to_save, f, indent=4)

        record["parsed"] = True
        record["last_modified"] = datetime.now().isoformat()
        metadata[resume_id] = record
        save_metadata(metadata)

        return structured_resume
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Re-parsing failed: {str(e)}"
        )

@router.get("/library/{resume_id}/data", status_code=status.HTTP_200_OK)
async def get_parsed_data(resume_id: str):
    """
    Load parsed JSON data instantly if it exists.
    """
    metadata = load_metadata()
    if resume_id not in metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    record = metadata[resume_id]
    json_path = record["json_path"]

    if not os.path.exists(json_path) or not record["parsed"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No parsed JSON data exists for this resume.")

    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load parsed JSON: {str(e)}"
        )

@router.post("/library/{resume_id}/rename", status_code=status.HTTP_200_OK)
async def rename_resume(resume_id: str, request: RenameRequest):
    """
    Rename an existing resume's display filename.
    """
    metadata = load_metadata()
    if resume_id not in metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    record = metadata[resume_id]
    
    # Ensure correct extension is kept
    ext = os.path.splitext(record["filename"])[1].lower()
    new_name = request.new_name
    if not new_name.lower().endswith(ext):
        new_name += ext

    record["filename"] = new_name
    record["last_modified"] = datetime.now().isoformat()
    metadata[resume_id] = record
    save_metadata(metadata)
    
    return {"message": "Resume renamed successfully", "record": record}

@router.post("/library/{resume_id}/save", status_code=status.HTTP_200_OK)
async def save_parsed_data(resume_id: str, data: Dict[str, Any]):
    """
    Save edited parsed JSON data back to disk.
    """
    metadata = load_metadata()
    if resume_id not in metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    record = metadata[resume_id]
    json_path = record["json_path"]

    try:
        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)
        
        record["last_modified"] = datetime.now().isoformat()
        metadata[resume_id] = record
        save_metadata(metadata)
        
        return {"message": "Parsed JSON saved successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save JSON: {str(e)}"
        )

@router.delete("/library/{resume_id}", status_code=status.HTTP_200_OK)
async def delete_resume(resume_id: str):
    """
    Delete a resume from library along with its uploads and parsed JSON files.
    """
    metadata = load_metadata()
    if resume_id not in metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    record = metadata[resume_id]
    file_path = record["file_path"]
    json_path = record["json_path"]

    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(json_path):
        os.remove(json_path)

    del metadata[resume_id]
    save_metadata(metadata)

    return {"message": "Resume deleted successfully"}

@router.get("/library/{resume_id}/download", status_code=status.HTTP_200_OK)
async def download_resume_original(resume_id: str):
    """
    Download the original uploaded resume file.
    """
    metadata = load_metadata()
    if resume_id not in metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    record = metadata[resume_id]
    file_path = record["file_path"]

    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing on disk.")

    return FileResponse(
        path=file_path,
        filename=record["filename"],
        media_type="application/octet-stream"
    )
