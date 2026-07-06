import pytest
from app.nlp.resume_parser import ResumeParser
from app.nlp.jd_parser import JDParser
from app.nlp.ats_scorer import ATSScorer
from app.nlp.skill_detector import SkillDetector
from app.services.auth_service import hash_password, verify_password
from tests.conftest import SAMPLE_RESUME_TEXT, SAMPLE_JD_TEXT


class TestResumeParser:
    def setup_method(self):
        self.parser = ResumeParser()

    def test_extract_email(self):
        result = self.parser.parse(SAMPLE_RESUME_TEXT)
        assert result["email"] == "john.smith@email.com"

    def test_extract_phone(self):
        result = self.parser.parse(SAMPLE_RESUME_TEXT)
        assert result["phone"] is not None

    def test_extract_linkedin(self):
        result = self.parser.parse(SAMPLE_RESUME_TEXT)
        assert "linkedin.com/in/johnsmith" in result["linkedin_url"]

    def test_extract_skills(self):
        result = self.parser.parse(SAMPLE_RESUME_TEXT)
        all_skills = [s.lower() for cat in result.get("skills", {}).values() for s in cat]
        assert any("python" in s for s in all_skills)
        assert any("react" in s for s in all_skills)

    def test_extract_experience(self):
        result = self.parser.parse(SAMPLE_RESUME_TEXT)
        assert len(result.get("experience", [])) >= 1

    def test_experience_years_calculated(self):
        result = self.parser.parse(SAMPLE_RESUME_TEXT)
        assert result.get("total_experience_years") is not None

    def test_empty_text(self):
        assert self.parser.parse("") == {}


class TestJDParser:
    def setup_method(self):
        self.parser = JDParser()

    def test_extract_required_skills(self):
        result = self.parser.parse(SAMPLE_JD_TEXT)
        skills_lower = [s.lower() for s in result.get("required_skills", [])]
        assert any("python" in s for s in skills_lower)

    def test_extract_experience(self):
        result = self.parser.parse(SAMPLE_JD_TEXT)
        assert "4" in (result.get("experience_required") or "")

    def test_extract_employment_type(self):
        result = self.parser.parse(SAMPLE_JD_TEXT)
        assert result.get("employment_type") == "full-time"

    def test_empty_jd(self):
        assert self.parser.parse("") == {}


class TestATSScorer:
    def setup_method(self):
        self.scorer = ATSScorer()

    def test_perfect_match_high_score(self):
        result = self.scorer.calculate_score(
            resume_text=SAMPLE_JD_TEXT, jd_text=SAMPLE_JD_TEXT,
            resume_skills=["Python", "React", "PostgreSQL", "Docker", "AWS"],
            jd_skills=["Python", "React", "PostgreSQL", "Docker", "AWS"],
            semantic_similarity=0.95, resume_experience_years=5, jd_experience_required="4+ years",
        )
        assert result["ats_score"] >= 75

    def test_score_range_0_to_100(self):
        for sim in [0.0, 0.5, 1.0]:
            result = self.scorer.calculate_score(
                resume_text="developer python react", jd_text="python react developer needed",
                resume_skills=["Python"], jd_skills=["Python", "React"],
                semantic_similarity=sim, resume_experience_years=3, jd_experience_required="3 years",
            )
            assert 0 <= result["ats_score"] <= 100

    def test_ats_grade(self):
        assert self.scorer.get_ats_grade(90)["grade"] == "A"
        assert self.scorer.get_ats_grade(20)["grade"] == "F"


class TestSkillDetector:
    def setup_method(self):
        self.detector = SkillDetector()

    def test_exact_skill_match(self):
        missing, matching = self.detector.detect_missing_skills(resume_skills=["Python", "React", "PostgreSQL"], jd_skills=["Python", "React", "PostgreSQL", "AWS"])
        assert "Python" in matching
        assert len(missing) == 1
        assert missing[0].skill == "AWS"

    def test_alias_matching(self):
        missing, _ = self.detector.detect_missing_skills(resume_skills=["postgres", "k8s"], jd_skills=["PostgreSQL", "Kubernetes"])
        assert len(missing) == 0

    def test_empty_jd_skills(self):
        missing, matching = self.detector.detect_missing_skills(resume_skills=["Python"], jd_skills=[])
        assert missing == []
        assert matching == []


class TestPasswordHashing:
    """Regression tests for the bcrypt 72-byte truncation bug that caused 500s on registration."""

    def test_normal_password_hashes_and_verifies(self):
        hashed = hash_password("TestPassword1")
        assert verify_password("TestPassword1", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("TestPassword1")
        assert not verify_password("WrongPassword1", hashed)

    def test_very_long_password_does_not_crash(self):
        # bcrypt has a hard 72-byte limit; a naive implementation raises here.
        long_password = "A1" + "x" * 200
        hashed = hash_password(long_password)
        assert verify_password(long_password, hashed)

    def test_unicode_password_does_not_crash(self):
        password = "Pässwörd123" + "😀" * 20
        hashed = hash_password(password)
        assert verify_password(password, hashed)
