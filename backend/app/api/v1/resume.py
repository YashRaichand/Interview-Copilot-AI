from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_user, rate_limiter
from app.models import User, Resume
from app.schemas import ResumeResponse, ResumeListItem, ResumeUploadResponse, MessageResponse
from app.services.resume_service import ResumeService
from app.config import settings

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(background_tasks: BackgroundTasks, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), _=Depends(rate_limiter)):
    if file.content_type not in ["application/pdf"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    file_data = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_data) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

    service = ResumeService(db)
    resume = await service.upload_resume(file_data=file_data, filename=file.filename or "resume.pdf", user_id=current_user.id)
    await db.commit()
    background_tasks.add_task(service.parse_resume_background, str(resume.id))
    return resume


@router.get("/", response_model=List[ResumeListItem])
async def list_resumes(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 20):
    result = await db.execute(select(Resume).where(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.delete("/{resume_id}", response_model=MessageResponse)
async def delete_resume(resume_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    service = ResumeService(db)
    await service.delete_resume(resume)
    await db.commit()
    return MessageResponse(message="Resume deleted successfully")


@router.post("/{resume_id}/reparse", response_model=MessageResponse)
async def reparse_resume(resume_id: UUID, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    service = ResumeService(db)
    background_tasks.add_task(service.parse_resume_background, str(resume_id))
    return MessageResponse(message="Resume parsing queued")
