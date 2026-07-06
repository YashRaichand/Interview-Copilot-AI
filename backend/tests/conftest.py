import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
import uuid

from app.main import app
from app.database import Base, get_db
from app.models import User
from app.services.auth_service import hash_password, create_token_pair
from app.config import settings

TEST_DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    user = User(id=uuid.uuid4(), email="test@example.com", full_name="Test User", hashed_password=hash_password("TestPassword1"), is_active=True, is_verified=True, role="user", auth_provider="local")
    db.add(user)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    tokens = create_token_pair(str(test_user.id))
    return {"Authorization": f"Bearer {tokens.access_token}"}


SAMPLE_RESUME_TEXT = """
John Smith
john.smith@email.com | +1-555-123-4567 | San Francisco, CA
linkedin.com/in/johnsmith | github.com/johnsmith

PROFESSIONAL SUMMARY
Experienced Software Engineer with 5 years of experience building scalable web applications.

SKILLS
Technical: Python, JavaScript, TypeScript, React, Next.js, FastAPI, Django
Databases: PostgreSQL, MongoDB, Redis
Cloud: AWS, Docker, Kubernetes, GitHub Actions

EXPERIENCE
Senior Software Engineer | TechCorp Inc | Jan 2022 - Present
• Developed RESTful APIs using FastAPI serving 10M+ requests/month
• Built React dashboard reducing customer support tickets by 40%

Software Engineer | StartupXYZ | Jun 2019 - Dec 2021
• Built full-stack e-commerce platform with Django and React

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley | 2019 | GPA: 3.8

PROJECTS
Interview Copilot AI | github.com/johnsmith/interview-copilot
AI-powered interview preparation platform using Python, FastAPI, React, PostgreSQL

CERTIFICATIONS
AWS Certified Solutions Architect - Associate | Amazon Web Services | 2023
"""

SAMPLE_JD_TEXT = """
Senior Software Engineer - Full Stack

TechCorp is looking for a Senior Software Engineer to join our growing team.

Requirements:
• 4+ years of software engineering experience
• Strong proficiency in Python and JavaScript/TypeScript
• Experience with React and Node.js
• PostgreSQL or similar relational database experience
• AWS or cloud platform experience
• Docker and containerization experience

Preferred:
• Kubernetes experience
• Redis or caching systems
• FastAPI or Django experience

Responsibilities:
• Design and build scalable backend APIs
• Collaborate with frontend team on React applications
• Optimize database queries and system performance

Benefits:
• Competitive salary $120k-$160k
• Full health/dental/vision

Employment Type: Full-time
Location: San Francisco, CA (Hybrid)
"""
