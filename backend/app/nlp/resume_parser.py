import re
import spacy
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SKILL_TAXONOMY = {
    "languages": ["python", "javascript", "typescript", "java", "c++", "c#", "c", "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "sql", "html", "css"],
    "frameworks": ["react", "next.js", "nextjs", "vue", "angular", "svelte", "django", "fastapi", "flask", "spring", "express", "node.js", "nodejs", "laravel", "rails", "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "pandas", "numpy", "tailwindcss", "tailwind", "bootstrap", "redux", "prisma", "sqlalchemy"],
    "databases": ["postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch", "sqlite", "oracle", "mssql", "dynamodb", "cassandra", "neo4j", "firebase", "supabase"],
    "cloud": ["aws", "gcp", "azure", "google cloud", "ec2", "s3", "lambda", "kubernetes", "k8s", "docker", "terraform", "ansible", "jenkins", "github actions", "gitlab ci", "heroku", "vercel", "netlify", "nginx", "kafka", "rabbitmq", "airflow"],
    "tools": ["git", "github", "gitlab", "jira", "confluence", "figma", "postman", "swagger", "linux", "unix", "vim", "vscode", "webpack", "vite", "pytest", "jest", "cypress", "selenium", "prometheus", "grafana"],
    "soft": ["leadership", "communication", "teamwork", "problem solving", "critical thinking", "agile", "scrum", "kanban", "project management", "mentoring", "collaboration", "time management"],
}

SECTION_HEADERS = {
    "experience": [r"(?:work\s+)?experience", r"employment\s+(?:history)?", r"professional\s+(?:background|experience)", r"work\s+history"],
    "education": [r"education(?:al\s+background)?", r"academic\s+(?:background|qualifications)", r"qualifications"],
    "skills": [r"(?:technical\s+)?skills?", r"core\s+competencies", r"technologies", r"tech\s+stack", r"expertise"],
    "projects": [r"projects?", r"personal\s+projects?", r"side\s+projects?", r"portfolio"],
    "certifications": [r"certifications?", r"certificates?", r"licenses?", r"achievements?", r"awards?"],
    "summary": [r"(?:professional\s+)?summary", r"profile", r"objective", r"about\s+me"],
}


class ResumeParser:
    def __init__(self):
        self._nlp = None

    def _get_nlp(self):
        if self._nlp is None:
            try:
                self._nlp = spacy.load("en_core_web_sm")
                logger.info("SpaCy en_core_web_sm loaded")
            except OSError:
                from spacy.lang.en import English
                self._nlp = English()
                logger.warning("Using blank English model — NER unavailable")
        return self._nlp

    def parse(self, text: str) -> dict:
        if not text or len(text.strip()) < 20:
            return {}

        nlp = self._get_nlp()
        doc = nlp(text[:100000])

        result = {
            "name": self._extract_name(doc, text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "location": self._extract_location(doc, text),
            "linkedin_url": self._extract_linkedin(text),
            "github_url": self._extract_github(text),
            "summary": self._extract_section(text, "summary"),
            "skills": self._extract_skills(text),
            "experience": self._extract_experience(text),
            "education": self._extract_education(text),
            "projects": self._extract_projects(text),
            "certifications": self._extract_certifications(text),
            "total_experience_years": None,
        }
        result["total_experience_years"] = self._calculate_experience_years(result["experience"])
        return result

    def _extract_name(self, doc, text: str) -> Optional[str]:
        first_chunk = text[:500]
        first_doc = self._get_nlp()(first_chunk)
        for ent in first_doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
                name = ent.text.strip()
                if not any(kw in name.lower() for kw in ["resume", "cv", "curriculum", "portfolio"]):
                    return name

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines[:5]:
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w) and not any(c.isdigit() for c in line) and "@" not in line and len(line) < 50:
                return line
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", text)
        return match.group(0).lower() if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        patterns = [r"(?:\+?\d{1,3}[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}", r"\+\d{10,15}"]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                phone = re.sub(r"[^\d+\-\(\)\s]", "", match.group(0)).strip()
                if len(re.sub(r"\D", "", phone)) >= 10:
                    return phone
        return None

    def _extract_location(self, doc, text: str) -> Optional[str]:
        gpe_entities = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
        if gpe_entities:
            return gpe_entities[0]
        match = re.search(r"(?:Location|Address|City)[:\s]+([A-Za-z\s,]+?)(?:\n|$)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        city_state = re.search(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*([A-Z]{2})\b", text)
        if city_state:
            return city_state.group(0)
        return None

    def _extract_linkedin(self, text: str) -> Optional[str]:
        match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+", text, re.IGNORECASE)
        if match:
            url = match.group(0)
            return url if url.startswith("http") else "https://" + url
        return None

    def _extract_github(self, text: str) -> Optional[str]:
        match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_]+", text, re.IGNORECASE)
        if match:
            url = match.group(0)
            return url if url.startswith("http") else "https://" + url
        return None

    def _get_section_text(self, text: str, section_key: str) -> Optional[str]:
        headers = SECTION_HEADERS.get(section_key, [])
        all_headers_pattern = "|".join(h for headers_list in SECTION_HEADERS.values() for h in headers_list)
        for header in headers:
            pattern = rf"(?:^|\n)[ \t]*(?:{header})[ \t]*:?[ \t]*\n(.*?)(?=\n[ \t]*(?:{all_headers_pattern})[ \t]*:?\s*\n|$)"
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return None

    def _extract_section(self, text: str, section_key: str) -> Optional[str]:
        section = self._get_section_text(text, section_key)
        return section[:2000] if section else None

    def _extract_skills(self, text: str) -> dict:
        text_lower = text.lower()
        found_skills = {cat: [] for cat in SKILL_TAXONOMY}

        for category, skills in SKILL_TAXONOMY.items():
            for skill in skills:
                if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                    display = self._format_skill(skill)
                    if display not in found_skills[category]:
                        found_skills[category].append(display)

        skills_section = self._get_section_text(text, "skills")
        if skills_section:
            additional = self._parse_skills_section(skills_section)
            for skill in additional:
                if skill not in found_skills.get("technical", []):
                    found_skills.setdefault("technical", []).append(skill)

        seen = set()
        for cat in found_skills:
            unique = []
            for skill in found_skills[cat]:
                lower = skill.lower()
                if lower not in seen:
                    seen.add(lower)
                    unique.append(skill)
            found_skills[cat] = unique
        return found_skills

    def _format_skill(self, skill: str) -> str:
        special_cases = {
            "javascript": "JavaScript", "typescript": "TypeScript", "python": "Python", "react": "React",
            "next.js": "Next.js", "nextjs": "Next.js", "nodejs": "Node.js", "node.js": "Node.js", "vue": "Vue.js",
            "postgresql": "PostgreSQL", "mongodb": "MongoDB", "mysql": "MySQL", "redis": "Redis", "aws": "AWS",
            "gcp": "GCP", "css": "CSS", "html": "HTML", "sql": "SQL", "c++": "C++", "c#": "C#",
            "fastapi": "FastAPI", "github": "GitHub",
        }
        return special_cases.get(skill.lower(), skill.title())

    def _parse_skills_section(self, section_text: str) -> list:
        text = re.sub(r"(?:languages?|frameworks?|tools?|technologies|skills?)\s*:\s*", "", section_text, flags=re.IGNORECASE)
        skills = re.split(r"[,|•\n\t]+", text)
        result = []
        for skill in skills:
            cleaned = skill.strip().strip("•-·").strip()
            if 2 <= len(cleaned) <= 50 and not cleaned.isdigit():
                result.append(cleaned)
        return result[:50]

    def _extract_experience(self, text: str) -> list:
        section = self._get_section_text(text, "experience")
        if not section:
            return []

        entries = []
        blocks = re.split(r"\n(?=(?:[A-Z][^\n]{0,60}\n|.+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4}).*))", section)
        date_pattern = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}|\d{4}"
        date_range_pattern = rf"({date_pattern})\s*[-–—to]+\s*({date_pattern}|Present|Current|Now)"

        for block in blocks:
            if len(block.strip()) < 10:
                continue
            lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
            if not lines:
                continue

            entry = {"company": None, "role": None, "start_date": None, "end_date": None, "duration": None, "description": None, "achievements": []}
            date_match = re.search(date_range_pattern, block, re.IGNORECASE)
            if date_match:
                entry["start_date"] = date_match.group(1)
                entry["end_date"] = date_match.group(2)
                entry["duration"] = f"{date_match.group(1)} - {date_match.group(2)}"

            if len(lines) >= 1:
                entry["role"] = lines[0]
            if len(lines) >= 2:
                entry["company"] = lines[1] if not re.search(date_range_pattern, lines[1], re.IGNORECASE) else lines[0]

            desc_lines = lines[2:]
            if date_match:
                desc_lines = [l for l in desc_lines if not re.search(date_range_pattern, l, re.IGNORECASE)]

            achievements = [l.lstrip("•-·*▪▸").strip() for l in desc_lines if l.startswith(("•", "-", "*", "▪", "▸"))]
            entry["achievements"] = achievements[:10]
            entry["description"] = " ".join(l for l in desc_lines if not l.startswith(("•", "-", "*", "▪", "▸")))[:500]

            if entry["role"] or entry["company"]:
                entries.append(entry)
        return entries[:10]

    def _extract_education(self, text: str) -> list:
        section = self._get_section_text(text, "education")
        if not section:
            return []

        degree_pattern = r"(?:Bachelor|Master|PhD|Ph\.D|B\.?S\.?|M\.?S\.?|B\.?E\.?|M\.?E\.?|B\.?Tech|M\.?Tech|B\.?A\.?|M\.?A\.?|MBA|Associate)[^\n]*"
        institution_keywords = ["university", "college", "institute", "school", "academy", "polytechnic"]
        entries = []
        lines = [l.strip() for l in section.split("\n") if l.strip()]

        i = 0
        while i < len(lines):
            entry = {"institution": None, "degree": None, "field": None, "graduation_year": None, "gpa": None}
            line = lines[i]

            degree_match = re.search(degree_pattern, line, re.IGNORECASE)
            if degree_match:
                entry["degree"] = degree_match.group(0).strip()
                field_match = re.search(r"(?:in|of)\s+([A-Za-z\s]+?)(?:\n|,|$)", line, re.IGNORECASE)
                if field_match:
                    entry["field"] = field_match.group(1).strip()

            if any(kw in line.lower() for kw in institution_keywords):
                entry["institution"] = line

            year_match = re.search(r"\b(20[0-2]\d|19[8-9]\d)\b", line)
            if year_match:
                entry["graduation_year"] = year_match.group(1)

            gpa_match = re.search(r"GPA[:\s]+(\d\.\d+)", line, re.IGNORECASE)
            if gpa_match:
                entry["gpa"] = gpa_match.group(1)

            if entry["degree"] or entry["institution"]:
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if not entry["institution"] and any(kw in next_line.lower() for kw in institution_keywords):
                        entry["institution"] = next_line
                        i += 1
                entries.append(entry)
            i += 1
        return entries[:5]

    def _extract_projects(self, text: str) -> list:
        section = self._get_section_text(text, "projects")
        if not section:
            return []

        entries = []
        blocks = re.split(r"\n(?=[A-Z•\-*])", section)
        for block in blocks:
            if len(block.strip()) < 10:
                continue
            lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
            if not lines:
                continue

            entry = {"name": lines[0].lstrip("•-*").strip(), "description": " ".join(lines[1:3]) if len(lines) > 1 else None, "tech_stack": [], "url": None, "github_url": None}
            tech_match = re.search(r"(?:Technologies?|Tech Stack|Built with|Stack)[:\s]+([^\n]+)", block, re.IGNORECASE)
            if tech_match:
                entry["tech_stack"] = [t.strip() for t in re.split(r"[,|/]", tech_match.group(1)) if t.strip()][:8]
            else:
                paren_match = re.search(r"\(([^)]+)\)", block)
                if paren_match:
                    entry["tech_stack"] = [t.strip() for t in re.split(r"[,/]", paren_match.group(1))][:8]

            github_match = re.search(r"github\.com/[A-Za-z0-9\-_/]+", block, re.IGNORECASE)
            if github_match:
                entry["github_url"] = "https://" + github_match.group(0)
            url_match = re.search(r"https?://[^\s\n]+", block)
            if url_match and "github" not in url_match.group(0).lower():
                entry["url"] = url_match.group(0)
            entries.append(entry)
        return entries[:8]

    def _extract_certifications(self, text: str) -> list:
        section = self._get_section_text(text, "certifications")
        if not section:
            return []
        entries = []
        lines = [l.strip() for l in section.split("\n") if l.strip()]
        for line in lines:
            line = line.lstrip("•-*·").strip()
            if len(line) < 3:
                continue
            entry = {"name": line, "issuer": None, "year": None, "url": None}
            year_match = re.search(r"\b(20[0-2]\d|19[9-9]\d)\b", line)
            if year_match:
                entry["year"] = year_match.group(1)
                entry["name"] = line[:year_match.start()].rstrip(" -,").strip()
            issuer_keywords = {"aws": "Amazon Web Services", "google": "Google", "microsoft": "Microsoft", "oracle": "Oracle", "cisco": "Cisco", "comptia": "CompTIA", "coursera": "Coursera", "udemy": "Udemy"}
            for keyword, issuer in issuer_keywords.items():
                if keyword in line.lower():
                    entry["issuer"] = issuer
                    break
            entries.append(entry)
        return entries[:10]

    def _calculate_experience_years(self, experience: list) -> Optional[float]:
        if not experience:
            return None
        total_months = 0
        current_year = datetime.now().year
        for exp in experience:
            if not exp.get("duration"):
                continue
            duration_text = exp["duration"].lower()
            is_current = any(w in duration_text for w in ["present", "current", "now"])
            years = re.findall(r"\b(20[0-2]\d|19[8-9]\d)\b", exp.get("duration", ""))
            if len(years) >= 2:
                start_year = int(years[0])
                end_year = current_year if is_current else int(years[1])
                total_months += (end_year - start_year) * 12
            elif len(years) == 1 and is_current:
                total_months += (current_year - int(years[0])) * 12
        if total_months == 0:
            return min(round(len(experience) * 1.5, 1), 20.0)
        return round(total_months / 12, 1)


resume_parser = ResumeParser()
