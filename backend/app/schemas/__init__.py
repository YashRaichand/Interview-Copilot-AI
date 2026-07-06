from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import enum


# ─── Enums ───────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    PREMIUM = "premium"

class QuestionType(str, enum.Enum):
    HR = "hr"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    PROJECT = "project"

class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class InterviewStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str


# ─── User Schemas ─────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None


# ─── Resume Schemas ───────────────────────────────────────────────────────────

class ExperienceEntry(BaseModel):
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    achievements: List[str] = []


class EducationEntry(BaseModel):
    institution: str
    degree: str
    field: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None


class ProjectEntry(BaseModel):
    name: str
    description: Optional[str] = None
    tech_stack: List[str] = []
    url: Optional[str] = None
    github_url: Optional[str] = None


class CertificationEntry(BaseModel):
    name: str
    issuer: Optional[str] = None
    year: Optional[str] = None
    url: Optional[str] = None


class SkillsData(BaseModel):
    technical: List[str] = []
    soft: List[str] = []
    languages: List[str] = []
    frameworks: List[str] = []
    tools: List[str] = []
    databases: List[str] = []
    cloud: List[str] = []


class ResumeUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    cloudinary_url: str
    is_parsed: bool
    created_at: datetime


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    cloudinary_url: str
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[SkillsData] = None
    experience: Optional[List[ExperienceEntry]] = None
    education: Optional[List[EducationEntry]] = None
    projects: Optional[List[ProjectEntry]] = None
    certifications: Optional[List[CertificationEntry]] = None
    total_experience_years: Optional[float] = None
    resume_category: Optional[str] = None
    is_parsed: bool
    created_at: datetime


class ResumeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    candidate_name: Optional[str] = None
    resume_category: Optional[str] = None
    is_parsed: bool
    created_at: datetime


# ─── Job Description Schemas ──────────────────────────────────────────────────

class JobDescriptionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    company: Optional[str] = None
    raw_text: str = Field(..., min_length=50)


class JobDescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: Optional[str] = None
    raw_text: str
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    experience_required: Optional[str] = None
    education_required: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    employment_type: Optional[str] = None
    location: Optional[str] = None
    is_parsed: bool
    created_at: datetime


# ─── Analysis Schemas ─────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    resume_id: UUID
    job_description_id: UUID


class ScoreBreakdown(BaseModel):
    keyword_match: float
    semantic_similarity: float
    skill_match: float
    experience_match: float
    weights: Dict[str, float]


class MissingSkill(BaseModel):
    skill: str
    priority: str
    category: str
    reason: str


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    job_description_id: UUID
    ats_score: Optional[float] = None
    skill_match_percentage: Optional[float] = None
    semantic_similarity: Optional[float] = None
    score_breakdown: Optional[ScoreBreakdown] = None
    missing_skills: Optional[List[MissingSkill]] = None
    matching_skills: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    success_probability: Optional[float] = None
    created_at: datetime


# ─── Interview Schemas ────────────────────────────────────────────────────────

class InterviewCreate(BaseModel):
    analysis_id: Optional[UUID] = None
    interview_type: str = "mixed"
    title: Optional[str] = "Mock Interview"
    num_questions: int = Field(default=10, ge=5, le=30)


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_text: str
    question_type: str
    difficulty: str
    category: Optional[str] = None
    order_index: int
    is_follow_up: bool


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: str
    interview_type: str
    overall_score: Optional[float] = None
    technical_score: Optional[float] = None
    communication_score: Optional[float] = None
    total_questions: int
    answered_questions: int
    duration_minutes: Optional[int] = None
    feedback_summary: Optional[str] = None
    improvement_areas: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    questions: List[QuestionResponse] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class InterviewListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: str
    interview_type: str
    overall_score: Optional[float] = None
    total_questions: int
    answered_questions: int
    created_at: datetime


# ─── Answer Schemas ───────────────────────────────────────────────────────────

class AnswerSubmit(BaseModel):
    question_id: UUID
    answer_text: str = Field(..., min_length=10)
    time_taken_seconds: Optional[int] = None


class AnswerEvaluation(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    relevance_score: float
    technical_accuracy_score: float
    completeness_score: float
    communication_score: float
    overall_score: float
    feedback: str
    improvement_suggestions: List[str]
    model_answer: Optional[str] = None
    keywords_used: List[str] = []
    keywords_missed: List[str] = []


class AnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    question_id: UUID
    answer_text: str
    relevance_score: Optional[float] = None
    technical_accuracy_score: Optional[float] = None
    completeness_score: Optional[float] = None
    communication_score: Optional[float] = None
    overall_score: Optional[float] = None
    feedback: Optional[str] = None
    improvement_suggestions: Optional[List[str]] = None
    model_answer: Optional[str] = None
    keywords_used: Optional[List[str]] = None
    keywords_missed: Optional[List[str]] = None
    created_at: datetime


# ─── Mock Interview Chat ──────────────────────────────────────────────────────

class MockInterviewMessage(BaseModel):
    interview_id: UUID
    message: str
    question_id: Optional[UUID] = None


class MockInterviewResponse(BaseModel):
    message: str
    question: Optional[QuestionResponse] = None
    evaluation: Optional[AnswerEvaluation] = None
    is_complete: bool = False
    next_action: str = "answer"


# ─── Roadmap Schemas ──────────────────────────────────────────────────────────

class WeekPlan(BaseModel):
    week: int
    focus: str
    topics: List[str]
    resources: List[Dict[str, str]]
    projects: List[str]
    goals: List[str]
    estimated_hours: int


class RoadmapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    duration_days: int
    weeks: Optional[List[WeekPlan]] = None
    skills_to_learn: Optional[List[str]] = None
    resources: Optional[List[Dict]] = None
    milestones: Optional[List[Dict]] = None
    progress_percentage: float
    completed_items: Optional[List[str]] = None
    is_active: bool
    created_at: datetime


class RoadmapProgressUpdate(BaseModel):
    completed_item_id: str
    is_completed: bool


# ─── Report Schemas ───────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    analysis_id: Optional[UUID] = None
    interview_id: Optional[UUID] = None
    report_type: str


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_type: str
    title: str
    cloudinary_url: Optional[str] = None
    created_at: datetime


# ─── Dashboard Schemas ────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_resumes: int
    total_analyses: int
    total_interviews: int
    best_ats_score: Optional[float] = None
    average_ats_score: Optional[float] = None
    latest_ats_score: Optional[float] = None
    latest_skill_match: Optional[float] = None
    success_probability: Optional[float] = None
    recent_interviews: List[InterviewListItem] = []
    ats_trend: List[Dict[str, Any]] = []
    missing_skills_summary: List[str] = []
    active_roadmap: Optional[RoadmapResponse] = None


# ─── Common ───────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True
