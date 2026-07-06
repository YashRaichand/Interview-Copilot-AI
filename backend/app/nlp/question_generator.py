import json
import logging
from typing import Optional
import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

QUESTION_TYPE_PROMPTS = {
    "hr": "HR/general interview questions about motivation, career goals, salary, culture fit, and work style",
    "technical": "Technical interview questions testing specific technology knowledge, coding concepts, and system design",
    "behavioral": "Behavioral questions using STAR method format about past experiences, conflicts, teamwork, and leadership",
    "project": "Questions about specific projects, technical decisions made, challenges overcome, and learnings",
}


class QuestionGenerator:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if not self._client:
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is not set")
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    async def generate(self, num_questions: int = 10, interview_type: str = "mixed", resume_text: Optional[str] = None, jd_text: Optional[str] = None, job_role: Optional[str] = None) -> list:
        type_distribution = self._get_type_distribution(interview_type, num_questions)
        all_questions = []

        for q_type, count in type_distribution.items():
            if count == 0:
                continue
            try:
                questions = await self._generate_for_type(q_type, count, resume_text, jd_text, job_role)
                all_questions.extend(questions)
            except Exception as e:
                logger.error(f"Failed to generate {q_type} questions: {e}")
                all_questions.extend(self._get_fallback_questions(q_type, count))

        return all_questions[:num_questions]

    async def _generate_for_type(self, q_type: str, count: int, resume_text: Optional[str], jd_text: Optional[str], job_role: Optional[str]) -> list:
        import asyncio

        context_parts = []
        if job_role:
            context_parts.append(f"Target Role: {job_role}")
        if resume_text:
            context_parts.append(f"Candidate Resume (truncated):\n{resume_text[:2000]}")
        if jd_text:
            context_parts.append(f"Job Description (truncated):\n{jd_text[:2000]}")
        context = "\n\n".join(context_parts) if context_parts else "No specific context provided."

        difficulties = self._distribute_difficulties(count)

        prompt = f"""You are an expert technical interviewer. Generate exactly {count} {QUESTION_TYPE_PROMPTS[q_type]}.

Context:
{context}

Requirements:
- Generate exactly {count} questions
- Mix of difficulties: {difficulties}
- Questions must be specific, not generic
- For technical questions, reference specific technologies from the resume/JD
- Each question should have 3-5 key points that a good answer should cover

Return ONLY a valid JSON array with this exact structure (no markdown, no explanation):
[
  {{
    "question": "The interview question text",
    "type": "{q_type}",
    "difficulty": "easy|medium|hard",
    "category": "specific sub-category",
    "key_points": ["Point 1", "Point 2", "Point 3"]
  }}
]"""

        client = self._get_client()
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: client.messages.create(model="claude-sonnet-4-6", max_tokens=2000, messages=[{"role": "user", "content": prompt}]))

        text = response.content[0].text.strip()
        try:
            questions = json.loads(text)
            if isinstance(questions, list):
                return questions[:count]
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))[:count]
                except Exception:
                    pass

        logger.warning(f"Failed to parse JSON for {q_type} questions, using fallback")
        return self._get_fallback_questions(q_type, count)

    def _get_type_distribution(self, interview_type: str, total: int) -> dict:
        distributions = {
            "mixed": {"technical": max(1, int(total * 0.4)), "behavioral": max(1, int(total * 0.3)), "hr": max(1, int(total * 0.2)), "project": max(1, int(total * 0.1))},
            "technical": {"technical": max(1, int(total * 0.7)), "project": max(1, int(total * 0.2)), "behavioral": max(1, int(total * 0.1)), "hr": 0},
            "hr": {"hr": max(1, int(total * 0.5)), "behavioral": max(1, int(total * 0.4)), "technical": max(1, int(total * 0.1)), "project": 0},
            "behavioral": {"behavioral": max(1, int(total * 0.6)), "hr": max(1, int(total * 0.3)), "technical": max(1, int(total * 0.1)), "project": 0},
        }
        dist = distributions.get(interview_type, distributions["mixed"])
        current = sum(dist.values())
        if current < total:
            dist["technical"] = dist.get("technical", 0) + (total - current)
        return dist

    def _distribute_difficulties(self, count: int) -> str:
        easy = max(1, count // 4)
        hard = max(1, count // 4)
        medium = count - easy - hard
        return f"{easy} easy, {medium} medium, {hard} hard"

    def _get_fallback_questions(self, q_type: str, count: int) -> list:
        fallbacks = {
            "hr": [
                {"question": "Tell me about yourself and your career journey.", "type": "hr", "difficulty": "easy", "category": "Introduction", "key_points": ["Background", "Career progression", "Motivation"]},
                {"question": "Why are you interested in this specific role?", "type": "hr", "difficulty": "easy", "category": "Motivation", "key_points": ["Company research", "Role alignment", "Career goals"]},
                {"question": "Where do you see yourself in 5 years?", "type": "hr", "difficulty": "medium", "category": "Career Goals", "key_points": ["Growth mindset", "Realistic goals"]},
                {"question": "How do you handle work-life balance?", "type": "hr", "difficulty": "easy", "category": "Work Style", "key_points": ["Time management", "Boundaries"]},
            ],
            "technical": [
                {"question": "Explain the difference between SQL and NoSQL databases and when to use each.", "type": "technical", "difficulty": "medium", "category": "Databases", "key_points": ["Schema flexibility", "Scalability", "Use case examples"]},
                {"question": "Explain REST API design principles and best practices.", "type": "technical", "difficulty": "medium", "category": "API Design", "key_points": ["HTTP methods", "Status codes", "Statelessness"]},
                {"question": "How does async/await work?", "type": "technical", "difficulty": "medium", "category": "Programming", "key_points": ["Event loop", "Non-blocking I/O"]},
                {"question": "Design a URL shortener system like bit.ly.", "type": "technical", "difficulty": "hard", "category": "System Design", "key_points": ["Hash function", "Database schema", "Scalability"]},
            ],
            "behavioral": [
                {"question": "Tell me about a time you handled a conflict with a team member.", "type": "behavioral", "difficulty": "medium", "category": "Conflict Resolution", "key_points": ["Situation", "Approach", "Resolution", "Outcome"]},
                {"question": "Describe a situation where you had to meet a tight deadline.", "type": "behavioral", "difficulty": "medium", "category": "Time Management", "key_points": ["Planning", "Prioritization", "Result"]},
                {"question": "Tell me about a time you took initiative without being asked.", "type": "behavioral", "difficulty": "medium", "category": "Initiative", "key_points": ["Problem identification", "Action", "Impact"]},
            ],
            "project": [
                {"question": "Walk me through your most complex technical project.", "type": "project", "difficulty": "hard", "category": "Technical Depth", "key_points": ["Architecture", "Challenges", "Results"]},
                {"question": "What is the most impactful bug you've ever fixed?", "type": "project", "difficulty": "medium", "category": "Debugging", "key_points": ["Discovery", "Root cause", "Fix approach"]},
            ],
        }
        questions = fallbacks.get(q_type, fallbacks["technical"])
        return questions[:count]


question_generator = QuestionGenerator()
