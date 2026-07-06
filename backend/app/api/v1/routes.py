from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_user, rate_limiter
from app.models import User, JobDescription, Analysis, Interview, Roadmap, Report
from app.schemas import (
    JobDescriptionCreate, JobDescriptionResponse, AnalysisRequest, AnalysisResponse,
    InterviewCreate, InterviewResponse, InterviewListItem, AnswerSubmit, AnswerResponse,
    MockInterviewMessage, MockInterviewResponse, RoadmapResponse, RoadmapProgressUpdate,
    ReportCreate, ReportResponse, DashboardStats, MessageResponse,
)

# ─── JD Router ───────────────────────────────────────────────────────────────

jd_router = APIRouter(prefix="/job-descriptions", tags=["Job Descriptions"])


@jd_router.post("/", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_jd(data: JobDescriptionCreate, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), _=Depends(rate_limiter)):
    from app.services.jd_service import JDService
    service = JDService(db)
    jd = await service.create_jd(data, current_user.id)
    await db.commit()
    background_tasks.add_task(service.parse_jd_background, str(jd.id))
    return jd


@jd_router.post("/upload", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def upload_jd_pdf(background_tasks: BackgroundTasks, title: str = "Job Description", company: Optional[str] = None, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), _=Depends(rate_limiter)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files accepted")
    file_data = await file.read()
    from app.services.jd_service import JDService
    service = JDService(db)
    jd = await service.upload_jd_pdf(file_data, file.filename, title, company, current_user.id)
    await db.commit()
    background_tasks.add_task(service.parse_jd_background, str(jd.id))
    return jd


@jd_router.get("/", response_model=List[JobDescriptionResponse])
async def list_jds(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 20):
    result = await db.execute(select(JobDescription).where(JobDescription.user_id == current_user.id).order_by(JobDescription.created_at.desc()).offset(skip).limit(limit))
    return result.scalars().all()


@jd_router.get("/{jd_id}", response_model=JobDescriptionResponse)
async def get_jd(jd_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JobDescription).where(JobDescription.id == jd_id, JobDescription.user_id == current_user.id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd


@jd_router.delete("/{jd_id}", response_model=MessageResponse)
async def delete_jd(jd_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JobDescription).where(JobDescription.id == jd_id, JobDescription.user_id == current_user.id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    await db.delete(jd)
    await db.commit()
    return MessageResponse(message="Job description deleted")


# ─── Analysis Router ─────────────────────────────────────────────────────────

analysis_router = APIRouter(prefix="/analyses", tags=["ATS Analysis"])


@analysis_router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def run_analysis(data: AnalysisRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), _=Depends(rate_limiter)):
    from app.services.analysis_service import AnalysisService
    service = AnalysisService(db)
    analysis = await service.run_full_analysis(data.resume_id, data.job_description_id, current_user.id)
    await db.commit()
    return analysis


@analysis_router.get("/", response_model=List[AnalysisResponse])
async def list_analyses(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 20):
    from app.models import Resume
    result = await db.execute(select(Analysis).join(Analysis.resume).where(Resume.user_id == current_user.id).order_by(Analysis.created_at.desc()).offset(skip).limit(limit))
    return result.scalars().all()


@analysis_router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models import Resume
    result = await db.execute(select(Analysis).join(Analysis.resume).where(Analysis.id == analysis_id, Resume.user_id == current_user.id))
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


# ─── Interview Router ─────────────────────────────────────────────────────────

interview_router = APIRouter(prefix="/interviews", tags=["Mock Interviews"])


@interview_router.post("/", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def create_interview(data: InterviewCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), _=Depends(rate_limiter)):
    from app.services.interview_service import InterviewService
    service = InterviewService(db)
    interview = await service.create_interview(data, current_user.id)
    await db.commit()
    return interview


@interview_router.get("/", response_model=List[InterviewListItem])
async def list_interviews(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 20):
    result = await db.execute(select(Interview).where(Interview.user_id == current_user.id).order_by(Interview.created_at.desc()).offset(skip).limit(limit))
    return result.scalars().all()


@interview_router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(interview_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Interview).where(Interview.id == interview_id, Interview.user_id == current_user.id))
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


@interview_router.post("/{interview_id}/answer", response_model=AnswerResponse)
async def submit_answer(interview_id: UUID, data: AnswerSubmit, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.services.interview_service import InterviewService
    service = InterviewService(db)
    answer = await service.submit_and_evaluate_answer(interview_id, data, current_user.id)
    await db.commit()
    return answer


@interview_router.post("/{interview_id}/complete", response_model=InterviewResponse)
async def complete_interview(interview_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.services.interview_service import InterviewService
    service = InterviewService(db)
    interview = await service.complete_interview(interview_id, current_user.id)
    await db.commit()
    return interview


@interview_router.post("/chat", response_model=MockInterviewResponse)
async def mock_interview_chat(data: MockInterviewMessage, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.services.interview_service import InterviewService
    service = InterviewService(db)
    response = await service.process_chat_message(data, current_user.id)
    await db.commit()
    return response


# ─── Roadmap Router ───────────────────────────────────────────────────────────

roadmap_router = APIRouter(prefix="/roadmaps", tags=["Learning Roadmaps"])


@roadmap_router.post("/generate", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
async def generate_roadmap(analysis_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), _=Depends(rate_limiter)):
    from app.services.roadmap_service import RoadmapService
    service = RoadmapService(db)
    roadmap = await service.generate_roadmap(analysis_id, current_user.id)
    await db.commit()
    return roadmap


@roadmap_router.get("/", response_model=List[RoadmapResponse])
async def list_roadmaps(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Roadmap).where(Roadmap.user_id == current_user.id).order_by(Roadmap.created_at.desc()))
    return result.scalars().all()


@roadmap_router.get("/active", response_model=RoadmapResponse)
async def get_active_roadmap(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Roadmap).where(Roadmap.user_id == current_user.id, Roadmap.is_active == True).order_by(Roadmap.created_at.desc()))
    roadmap = result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=404, detail="No active roadmap found")
    return roadmap


@roadmap_router.patch("/{roadmap_id}/progress", response_model=RoadmapResponse)
async def update_progress(roadmap_id: UUID, data: RoadmapProgressUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.services.roadmap_service import RoadmapService
    service = RoadmapService(db)
    roadmap = await service.update_progress(roadmap_id, data, current_user.id)
    await db.commit()
    return roadmap


# ─── Reports Router ───────────────────────────────────────────────────────────

reports_router = APIRouter(prefix="/reports", tags=["Reports"])


@reports_router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(data: ReportCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), _=Depends(rate_limiter)):
    from app.services.report_service import ReportService
    service = ReportService(db)
    report = await service.generate_report(data, current_user.id)
    await db.commit()
    return report


@reports_router.get("/", response_model=List[ReportResponse])
async def list_reports(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.user_id == current_user.id).order_by(Report.created_at.desc()))
    return result.scalars().all()


# ─── Dashboard Router ─────────────────────────────────────────────────────────

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard_router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.services.dashboard_service import DashboardService
    service = DashboardService(db)
    return await service.get_stats(current_user.id)
