from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import io
from services.export_service import DocumentExportService
from models.resume_schema import ResumeSchema

router = APIRouter()
export_service = DocumentExportService()

@router.post("/pdf", status_code=status.HTTP_200_OK)
async def export_pdf(resume: ResumeSchema):
    """
    Export structured resume JSON as a premium, styled PDF file stream.
    """
    try:
        pdf_bytes = await export_service.export_to_pdf(resume)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=resume_{resume.contact_info.name.replace(' ', '_')}.pdf"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )

@router.post("/docx", status_code=status.HTTP_200_OK)
async def export_docx(resume: ResumeSchema):
    """
    Export structured resume JSON as a standard Microsoft Word file stream.
    """
    try:
        docx_bytes = export_service.export_to_docx(resume)
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=resume_{resume.contact_info.name.replace(' ', '_')}.docx"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Word document: {str(e)}"
        )
