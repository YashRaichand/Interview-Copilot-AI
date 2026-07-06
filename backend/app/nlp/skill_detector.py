import logging
from typing import Optional
from app.schemas import MissingSkill

logger = logging.getLogger(__name__)

HIGH_DEMAND_SKILLS = {"python", "typescript", "react", "kubernetes", "terraform", "aws", "machine learning", "deep learning", "llm", "langchain", "fastapi", "nextjs", "next.js", "postgresql", "redis", "docker", "ci/cd", "graphql", "rust", "go", "golang"}

SKILL_CATEGORIES = {
    "Python": "Programming Language", "JavaScript": "Programming Language", "TypeScript": "Programming Language",
    "Java": "Programming Language", "C++": "Programming Language", "C#": "Programming Language", "Go": "Programming Language",
    "React": "Frontend Framework", "Vue.js": "Frontend Framework", "Angular": "Frontend Framework", "Next.js": "Frontend Framework",
    "TailwindCSS": "CSS Framework", "FastAPI": "Backend Framework", "Django": "Backend Framework", "Flask": "Backend Framework",
    "Express": "Backend Framework", "Node.js": "Runtime Environment", "TensorFlow": "ML Framework", "PyTorch": "ML Framework",
    "PostgreSQL": "Database", "MySQL": "Database", "MongoDB": "Database", "Redis": "Cache/Database",
    "AWS": "Cloud Platform", "GCP": "Cloud Platform", "Azure": "Cloud Platform", "Docker": "Containerization",
    "Kubernetes": "Orchestration", "Terraform": "Infrastructure as Code", "GraphQL": "API Technology", "Git": "Version Control",
}


class SkillDetector:
    def detect_missing_skills(self, resume_skills: list, jd_skills: list, required_skills: Optional[list] = None, preferred_skills: Optional[list] = None) -> tuple:
        if not jd_skills:
            return [], []

        resume_normalized = self._normalize_skills(resume_skills)
        required_set = self._normalize_skills(required_skills or [])
        preferred_set = self._normalize_skills(preferred_skills or [])

        missing = []
        matching = []

        for skill in jd_skills:
            normalized = skill.lower().strip()
            if self._skill_in_resume(normalized, resume_normalized):
                matching.append(skill)
            else:
                priority = self._calculate_priority(normalized, normalized in required_set, normalized in preferred_set)
                category = self._get_category(skill)
                reason = self._get_reason(skill, priority)
                missing.append(MissingSkill(skill=skill, priority=priority, category=category, reason=reason))

        priority_order = {"high": 0, "medium": 1, "low": 2}
        missing.sort(key=lambda x: priority_order.get(x.priority, 3))
        return missing, matching

    def _normalize_skills(self, skills: list) -> set:
        normalized = set()
        for skill in skills:
            lower = skill.lower().strip()
            normalized.add(lower)
            normalized.update(self._get_aliases(lower))
        return normalized

    def _skill_in_resume(self, skill: str, resume_set: set) -> bool:
        if skill in resume_set:
            return True
        for resume_skill in resume_set:
            if len(skill) > 3 and (skill in resume_skill or resume_skill in skill):
                return True
        aliases = self._get_aliases(skill)
        return bool(aliases & resume_set)

    def _get_aliases(self, skill: str) -> set:
        alias_map = {
            "javascript": {"js", "ecmascript"}, "typescript": {"ts"}, "python": {"py"},
            "postgresql": {"postgres", "psql"}, "kubernetes": {"k8s"}, "next.js": {"nextjs", "next js"},
            "node.js": {"nodejs", "node js"}, "vue.js": {"vue", "vuejs"}, "react.js": {"react", "reactjs"},
            "machine learning": {"ml"}, "deep learning": {"dl"}, "ci/cd": {"cicd", "ci cd"},
            "amazon web services": {"aws"}, "google cloud platform": {"gcp"}, "tensorflow": {"tf"},
        }
        return alias_map.get(skill, set())

    def _calculate_priority(self, skill: str, is_required: bool, is_preferred: bool) -> str:
        if is_required or skill.lower() in HIGH_DEMAND_SKILLS:
            return "high"
        elif is_preferred:
            return "medium"
        return "low"

    def _get_category(self, skill: str) -> str:
        for key, category in SKILL_CATEGORIES.items():
            if key.lower() == skill.lower():
                return category
        for key, category in SKILL_CATEGORIES.items():
            if key.lower() in skill.lower() or skill.lower() in key.lower():
                return category
        return "Technical Skill"

    def _get_reason(self, skill: str, priority: str) -> str:
        reasons = {
            "high": f"{skill} is a core requirement for this role and frequently appears in the job description.",
            "medium": f"{skill} is preferred by the employer and could differentiate your application.",
            "low": f"Adding {skill} would strengthen your profile for similar roles.",
        }
        return reasons.get(priority, f"Learning {skill} would improve your qualifications.")


skill_detector = SkillDetector()
