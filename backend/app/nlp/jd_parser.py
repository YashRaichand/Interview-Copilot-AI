import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)

REQUIRED_SKILL_SIGNALS = [r"required(?:\s+skills?)?", r"must\s+have", r"essential", r"mandatory", r"you\s+(?:must|should|need\s+to)\s+have", r"requirements?", r"qualifications?", r"we\s+(?:require|need|expect)"]
PREFERRED_SKILL_SIGNALS = [r"preferred(?:\s+skills?)?", r"nice\s+to\s+have", r"bonus", r"desired", r"plus", r"advantageous", r"ideally", r"would\s+be\s+(?:a\s+)?(?:plus|bonus|great|ideal)"]
EXPERIENCE_PATTERNS = [r"(\d+)\+?\s*(?:to|-|–)\s*(\d+)\s*years?\s+(?:of\s+)?(?:experience|exp)", r"(\d+)\+\s*years?\s+(?:of\s+)?(?:experience|exp)", r"(\d+)\s*years?\s+(?:of\s+)?(?:experience|exp)", r"minimum\s+(\d+)\s*years?", r"at\s+least\s+(\d+)\s*years?"]
EDUCATION_PATTERNS = [r"(?:Bachelor(?:'s)?|BS|B\.?S\.?|B\.?E\.?|B\.?Tech)\s+(?:degree\s+)?(?:in\s+[A-Za-z\s]+)?", r"(?:Master(?:'s)?|MS|M\.?S\.?|M\.?E\.?|M\.?Tech|MBA)\s+(?:degree\s+)?(?:in\s+[A-Za-z\s]+)?", r"(?:PhD|Ph\.D)\s+(?:in\s+[A-Za-z\s]+)?", r"(?:degree\s+in\s+[A-Za-z\s]+)", r"(?:Computer Science|Software Engineering|Information Technology|Engineering)"]
EMPLOYMENT_TYPES = {"full-time": ["full-time", "full time", "permanent", "regular"], "part-time": ["part-time", "part time"], "contract": ["contract", "freelance", "temporary", "contingent"], "remote": ["remote", "work from home", "wfh", "distributed"], "hybrid": ["hybrid", "flexible"], "on-site": ["on-site", "onsite", "in-office", "in office"]}
TECH_SKILLS_COMMON = ["python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "ruby", "react", "angular", "vue", "next.js", "node.js", "django", "flask", "fastapi", "spring", "express", "tensorflow", "pytorch", "keras", "scikit-learn", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb", "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "git", "rest api", "graphql", "microservices", "sql", "nosql", "html", "css", "machine learning", "deep learning", "nlp", "computer vision", "data science", "agile", "scrum", "ci/cd", "devops", "linux", "bash", "kafka", "rabbitmq", "spark", "hadoop", "airflow", "pandas", "numpy", "data engineering", "mobile", "ios", "android", "swift", "kotlin", "flutter", "react native", "firebase"]


class JDParser:
    def parse(self, text: str) -> dict:
        if not text or len(text.strip()) < 20:
            return {}
        return {
            "required_skills": self._extract_required_skills(text),
            "preferred_skills": self._extract_preferred_skills(text),
            "experience_required": self._extract_experience(text),
            "education_required": self._extract_education(text),
            "responsibilities": self._extract_responsibilities(text),
            "benefits": self._extract_benefits(text),
            "employment_type": self._extract_employment_type(text),
            "location": self._extract_location(text),
            "salary_range": self._extract_salary(text),
        }

    def _extract_required_skills(self, text: str) -> list:
        text_lower = text.lower()
        required_section = self._get_section_by_signals(text, REQUIRED_SKILL_SIGNALS)
        preferred_section = self._get_section_by_signals(text, PREFERRED_SKILL_SIGNALS)

        required_skills = set()
        if required_section:
            for skill in TECH_SKILLS_COMMON:
                if re.search(r"\b" + re.escape(skill) + r"\b", required_section.lower()):
                    required_skills.add(self._format_skill(skill))

        all_skills = set()
        for skill in TECH_SKILLS_COMMON:
            if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                all_skills.add(self._format_skill(skill))

        preferred_skills = set()
        if preferred_section:
            for skill in TECH_SKILLS_COMMON:
                if re.search(r"\b" + re.escape(skill) + r"\b", preferred_section.lower()):
                    preferred_skills.add(self._format_skill(skill))

        if required_section:
            return sorted(required_skills)[:20]
        return sorted(all_skills - preferred_skills)[:20]

    def _extract_preferred_skills(self, text: str) -> list:
        preferred_section = self._get_section_by_signals(text, PREFERRED_SKILL_SIGNALS)
        if not preferred_section:
            return []
        preferred = set()
        for skill in TECH_SKILLS_COMMON:
            if re.search(r"\b" + re.escape(skill) + r"\b", preferred_section.lower()):
                preferred.add(self._format_skill(skill))
        return sorted(preferred)[:15]

    def _get_section_by_signals(self, text: str, signals: list) -> Optional[str]:
        combined_signal = "|".join(signals)
        pattern = rf"(?:{combined_signal})[:\s]*((?:.|\n){{10,400}}?)(?=\n\n|\Z)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
        for signal in signals:
            pattern2 = rf"(?:{signal})[:\s]*\n((?:\s*[-•*]\s*.+\n?){{1,20}})"
            m2 = re.search(pattern2, text, re.IGNORECASE)
            if m2:
                return m2.group(0)
        return None

    def _extract_experience(self, text: str) -> Optional[str]:
        for pattern in EXPERIENCE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None

    def _extract_education(self, text: str) -> Optional[str]:
        for pattern in EDUCATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = match.group(0).strip().rstrip(".,")
                if len(result) > 3:
                    return result
        return None

    def _extract_responsibilities(self, text: str) -> list:
        resp_headers = [r"responsibilities", r"what\s+you(?:'ll)?\s+(?:do|be\s+doing|own)", r"job\s+duties", r"role\s+(?:and\s+)?responsibilities", r"key\s+(?:responsibilities|duties)", r"you\s+will"]
        combined = "|".join(resp_headers)
        pattern = rf"(?:{combined})[:\s]*((?:.|\n){{50,1500}}?)(?=\n\n|\n[A-Z]|\Z)"
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return []
        section = match.group(1)
        bullets = re.findall(r"(?:^|\n)\s*[-•*▪✓]\s*(.+)", section)
        if bullets:
            return [b.strip() for b in bullets if len(b.strip()) > 5][:15]
        sentences = re.split(r"[.\n]", section)
        return [s.strip() for s in sentences if len(s.strip()) > 10][:10]

    def _extract_benefits(self, text: str) -> list:
        benefit_headers = [r"benefits?", r"perks?", r"what\s+we\s+offer", r"compensation", r"we\s+provide", r"you(?:'ll)?\s+(?:get|receive)"]
        combined = "|".join(benefit_headers)
        pattern = rf"(?:{combined})[:\s]*((?:.|\n){{50,600}}?)(?=\n\n|\Z)"
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return []
        section = match.group(1)
        bullets = re.findall(r"(?:^|\n)\s*[-•*]\s*(.+)", section)
        return [b.strip() for b in bullets if len(b.strip()) > 3][:10]

    def _extract_employment_type(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for emp_type, keywords in EMPLOYMENT_TYPES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return emp_type
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        patterns = [r"(?:Location|Based in|Office)\s*:\s*([A-Za-z\s,]+?)(?:\n|$)", r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z]{2})\b", r"\b(Remote(?:\s*[-/]\s*[A-Za-z\s]+)?)\b", r"\b([A-Z][a-z]+,\s*(?:USA|UK|India|Canada|Australia|Germany|Singapore))\b"]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_salary(self, text: str) -> Optional[str]:
        patterns = [r"\$\d{2,3}[,k]?\d*(?:\s*[-–]\s*\$\d{2,3}[,k]?\d*)?(?:\s*(?:per\s+year|annually|\/yr|k\/year))?", r"(?:salary|compensation|pay)\s*:\s*([^\n]{5,50})", r"(?:USD|EUR|GBP)\s*\d+[,k]?\d*(?:\s*[-–]\s*\d+[,k]?\d*)?"]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()[:100]
        return None

    def _format_skill(self, skill: str) -> str:
        special_cases = {"javascript": "JavaScript", "typescript": "TypeScript", "python": "Python", "react": "React", "node.js": "Node.js", "next.js": "Next.js", "postgresql": "PostgreSQL", "mongodb": "MongoDB", "mysql": "MySQL", "redis": "Redis", "aws": "AWS", "gcp": "GCP", "css": "CSS", "html": "HTML", "sql": "SQL", "c++": "C++", "c#": "C#", "graphql": "GraphQL", "fastapi": "FastAPI", "rest api": "REST API", "ci/cd": "CI/CD", "nosql": "NoSQL"}
        return special_cases.get(skill.lower(), skill.title())


jd_parser = JDParser()
