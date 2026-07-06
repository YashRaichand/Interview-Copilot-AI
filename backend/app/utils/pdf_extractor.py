import pdfplumber
import io
import re
import logging

logger = logging.getLogger(__name__)


class PDFExtractor:
    def extract_text(self, file_data: bytes) -> str:
        try:
            with pdfplumber.open(io.BytesIO(file_data)) as pdf:
                pages_text = []
                for page in pdf.pages:
                    text = page.extract_text(x_tolerance=3, y_tolerance=3)
                    if text:
                        pages_text.append(text)
                full_text = "\n\n".join(pages_text)
                return self._clean_text(full_text)
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise ValueError(f"Could not extract text from PDF: {e}")

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("\x00", "")
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\r", "\n", text)
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                cleaned_lines.append(stripped)
            elif cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
        text = "\n".join(cleaned_lines)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def validate_pdf(self, file_data: bytes) -> tuple[bool, str]:
        if len(file_data) < 4:
            return False, "File is too small"
        if not file_data.startswith(b"%PDF"):
            return False, "File is not a valid PDF"
        try:
            with pdfplumber.open(io.BytesIO(file_data)) as pdf:
                if len(pdf.pages) == 0:
                    return False, "PDF has no pages"
                first_page_text = pdf.pages[0].extract_text()
                if not first_page_text or len(first_page_text.strip()) < 10:
                    return False, "PDF appears to be scanned/image-only and cannot be parsed"
            return True, "Valid PDF"
        except Exception as e:
            return False, f"PDF validation failed: {e}"


pdf_extractor = PDFExtractor()
