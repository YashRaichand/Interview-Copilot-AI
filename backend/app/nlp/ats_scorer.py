import re
import logging

logger = logging.getLogger(__name__)

WEIGHTS = {"keyword": 0.30, "semantic": 0.30, "skill": 0.25, "experience": 0.15}
ATS_KEYWORDS_BOOST = ["experience", "skills", "proficient", "expertise", "knowledge", "developed", "implemented", "designed", "built", "managed", "led", "created", "maintained", "optimized", "deployed", "collaborated", "delivered", "achieved", "improved", "increased"]
STOP_WORDS = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "up", "about", "into", "through", "during", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "shall", "can", "need", "dare", "ought", "used", "able"}


class ATSScorer:
    def calculate_score(self, resume_text: str, jd_text: str, resume_skills: list, jd_skills: list, semantic_similarity: float, resume_experience_years: float, jd_experience_required: str) -> dict:
        keyword_score = self._keyword_match_score(resume_text, jd_text)
        semantic_score = min(semantic_similarity * 100, 100)
        skill_score = self._skill_match_score(resume_skills, jd_skills)
        experience_score = self._experience_match_score(resume_experience_years, jd_experience_required)

        ats_score = keyword_score * WEIGHTS["keyword"] + semantic_score * WEIGHTS["semantic"] + skill_score * WEIGHTS["skill"] + experience_score * WEIGHTS["experience"]
        ats_score = round(min(max(ats_score, 0), 100), 1)

        breakdown = {
            "keyword_match": round(keyword_score, 1), "semantic_similarity": round(semantic_score, 1),
            "skill_match": round(skill_score, 1), "experience_match": round(experience_score, 1),
            "weights": WEIGHTS,
        }

        recommendations = self._generate_recommendations(ats_score, keyword_score, skill_score, experience_score, semantic_score)

        return {
            "ats_score": ats_score, "keyword_score": round(keyword_score, 1), "skill_score": round(skill_score, 1),
            "experience_score": round(experience_score, 1), "breakdown": breakdown, "recommendations": recommendations,
        }

    def _keyword_match_score(self, resume_text: str, jd_text: str) -> float:
        resume_tokens = self._tokenize(resume_text)
        jd_tokens = self._tokenize(jd_text)
        if not jd_tokens:
            return 0.0

        jd_freq = {}
        for token in jd_tokens:
            jd_freq[token] = jd_freq.get(token, 0) + 1

        resume_set = set(resume_tokens)
        total_weight = 0.0
        matched_weight = 0.0
        for token, freq in jd_freq.items():
            boost = 1.5 if token in ATS_KEYWORDS_BOOST else 1.0
            weight = freq * boost
            total_weight += weight
            if token in resume_set:
                matched_weight += weight

        if total_weight == 0:
            return 0.0
        raw_score = matched_weight / total_weight
        return round(min(raw_score / 0.40, 1.0) * 100, 1)

    def _skill_match_score(self, resume_skills: list, jd_skills: list) -> float:
        if not jd_skills:
            return 75.0
        resume_lower = {s.lower().strip() for s in resume_skills}
        jd_lower = [s.lower().strip() for s in jd_skills]
        matched = 0
        for skill in jd_lower:
            if skill in resume_lower:
                matched += 1
            elif any(skill in rs or rs in skill for rs in resume_lower if len(skill) > 3):
                matched += 0.7
        score = (matched / len(jd_lower)) * 100
        return round(min(score, 100), 1)

    def _experience_match_score(self, resume_years: float, jd_experience_str: str) -> float:
        if not jd_experience_str or resume_years is None:
            return 70.0
        numbers = re.findall(r"\d+", jd_experience_str)
        if not numbers:
            return 70.0
        required_min = int(numbers[0])
        required_max = int(numbers[1]) if len(numbers) > 1 else required_min + 2
        if resume_years >= required_min:
            return 100.0 if resume_years <= required_max + 3 else 85.0
        ratio = resume_years / required_min
        return round(ratio * 80, 1)

    def _tokenize(self, text: str) -> list:
        text = text.lower()
        tokens = re.findall(r"\b[a-z][a-z0-9\+\#\.]{1,30}\b", text)
        return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]

    def _generate_recommendations(self, ats_score, keyword_score, skill_score, experience_score, semantic_score) -> list:
        recs = []
        if keyword_score < 50:
            recs.append("Add more keywords from the job description to your resume — especially in the summary and experience sections.")
        if skill_score < 60:
            recs.append("Your technical skill match is low. Focus on learning and adding the missing required skills to your profile.")
        if experience_score < 60:
            recs.append("Highlight relevant experience more prominently. Consider adding projects or freelance work to compensate for experience gaps.")
        if semantic_score < 50:
            recs.append("Align your resume language more closely with the job description. Mirror the terminology and phrasing used in the JD.")
        if ats_score >= 80:
            recs.append("Great ATS match! Prepare thoroughly for the technical interview round — your resume will pass screening.")
        elif ats_score >= 60:
            recs.append("Decent ATS score. Strengthen weak areas before applying to maximize your chances of interview selection.")
        else:
            recs.append("Your ATS score is below the typical 60% threshold. Consider tailoring your resume specifically for this role.")
        recs.append("Quantify your achievements with numbers (e.g., 'Improved API response time by 40%', 'Managed team of 5 engineers').")
        recs.append("Use action verbs at the start of bullet points: built, designed, optimized, delivered, automated, led.")
        return recs[:5]

    def get_ats_grade(self, score: float) -> dict:
        if score >= 85:
            return {"grade": "A", "label": "Excellent", "color": "#10b981", "message": "Strong ATS match — likely to pass screening"}
        elif score >= 70:
            return {"grade": "B", "label": "Good", "color": "#3b82f6", "message": "Good match — resume will likely pass ATS"}
        elif score >= 55:
            return {"grade": "C", "label": "Average", "color": "#f59e0b", "message": "Average match — some tailoring needed"}
        elif score >= 40:
            return {"grade": "D", "label": "Below Average", "color": "#f97316", "message": "Significant gaps — resume needs work"}
        return {"grade": "F", "label": "Poor", "color": "#ef4444", "message": "Poor match — consider a different role or extensive resume update"}


ats_scorer = ATSScorer()
