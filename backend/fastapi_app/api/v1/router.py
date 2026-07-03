from fastapi import APIRouter
from api.v1.parse import router as parse_router
from api.v1.ats import router as ats_router
from api.v1.chat import router as chat_router
from api.v1.jobs import router as jobs_router
from api.v1.exports import router as exports_router

api_router = APIRouter()
api_router.include_router(parse_router, prefix="/parse", tags=["Parser"])
api_router.include_router(ats_router, prefix="/ats", tags=["ATS"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(exports_router, prefix="/exports", tags=["Exports"])
