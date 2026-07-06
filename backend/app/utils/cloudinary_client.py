import cloudinary
import cloudinary.uploader
import cloudinary.utils
from app.config import settings
import logging
import io

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


class CloudinaryClient:
    RESUME_FOLDER = "interview_copilot/resumes"
    JD_FOLDER = "interview_copilot/job_descriptions"
    REPORT_FOLDER = "interview_copilot/reports"

    async def upload_pdf(self, file_data: bytes, filename: str, folder: str, user_id: str) -> dict:
        try:
            public_id = f"{folder}/{user_id}/{filename.replace('.pdf', '')}"
            result = cloudinary.uploader.upload(
                io.BytesIO(file_data),
                public_id=public_id,
                resource_type="raw",
                format="pdf",
                folder=folder,
                overwrite=True,
                tags=["interview_copilot", f"user_{user_id}"],
            )
            logger.info(f"Uploaded PDF to Cloudinary: {result['public_id']}")
            return {"url": result["secure_url"], "public_id": result["public_id"]}
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            raise

    async def upload_resume(self, file_data: bytes, filename: str, user_id: str) -> dict:
        return await self.upload_pdf(file_data, filename, self.RESUME_FOLDER, user_id)

    async def upload_jd(self, file_data: bytes, filename: str, user_id: str) -> dict:
        return await self.upload_pdf(file_data, filename, self.JD_FOLDER, user_id)

    async def delete_file(self, public_id: str, resource_type: str = "raw") -> bool:
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            return result.get("result") == "ok"
        except Exception as e:
            logger.error(f"Cloudinary delete failed for {public_id}: {e}")
            return False


cloudinary_client = CloudinaryClient()
