from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import logging

from app.models import Resume
from app.utils.cloudinary_client import cloudinary_client
from app.utils.pdf_extractor import pdf_extractor
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ResumeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_resume(self, file_data: bytes, filename: str, user_id: UUID) -> Resume:
        is_valid, reason = pdf_extractor.validate_pdf(file_data)
        if not is_valid:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=reason)

        try:
            upload_result = await cloudinary_client.upload_resume(file_data, filename, str(user_id))
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            upload_result = {"url": f"local://{filename}", "public_id": f"local/{str(user_id)}/{filename}"}

        try:
            raw_text = pdf_extractor.extract_text(file_data)
        except Exception as e:
            logger.warning(f"PDF text extraction failed: {e}")
            raw_text = None

        resume = Resume(
            user_id=user_id,
            filename=filename,
            cloudinary_url=upload_result["url"],
            cloudinary_public_id=upload_result["public_id"],
            raw_text=raw_text,
            is_parsed=False,
        )
        self.db.add(resume)
        await self.db.flush()
        return resume

    async def parse_resume_background(self, resume_id: str):
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(select(Resume).where(Resume.id == UUID(resume_id)))
                resume = result.scalar_one_or_none()
                if not resume or not resume.raw_text:
                    return

                from app.nlp.resume_parser import resume_parser
                parsed = resume_parser.parse(resume.raw_text)

                resume.candidate_name = parsed.get("name")
                resume.email = parsed.get("email")
                resume.phone = parsed.get("phone")
                resume.location = parsed.get("location")
                resume.linkedin_url = parsed.get("linkedin_url")
                resume.github_url = parsed.get("github_url")
                resume.summary = parsed.get("summary")
                resume.skills = parsed.get("skills", {})
                resume.experience = parsed.get("experience", [])
                resume.education = parsed.get("education", [])
                resume.projects = parsed.get("projects", [])
                resume.certifications = parsed.get("certifications", [])
                resume.total_experience_years = parsed.get("total_experience_years")

                try:
                    from app.nlp.semantic_matcher import semantic_matcher
                    embedding = await semantic_matcher.encode(resume.raw_text)
                    resume.embedding = embedding.tolist()
                except Exception as e:
                    logger.warning(f"Embedding generation failed: {e}")

                try:
                    from app.ml.resume_classifier import resume_classifier
                    resume.resume_category = resume_classifier.predict(resume.raw_text)
                except Exception as e:
                    logger.warning(f"Resume classification failed: {e}")

                resume.is_parsed = True
                await db.commit()
                logger.info(f"Resume {resume_id} parsed successfully")
            except Exception as e:
                logger.error(f"Background parsing failed for {resume_id}: {e}")
                await db.rollback()

    async def delete_resume(self, resume: Resume):
        try:
            if not resume.cloudinary_public_id.startswith("local/"):
                await cloudinary_client.delete_file(resume.cloudinary_public_id)
        except Exception as e:
            logger.warning(f"Failed to delete Cloudinary file: {e}")
        await self.db.delete(resume)
