import json
import asyncio
import logging
from typing import Optional
import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


class RoadmapGenerator:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if not self._client:
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    async def generate(self, missing_skills: list, target_role: Optional[str] = None, current_role: Optional[str] = None, ats_score: float = 0.0) -> dict:
        try:
            return await self._claude_generate(missing_skills, target_role, current_role, ats_score)
        except Exception as e:
            logger.error(f"Roadmap generation failed: {e}")
            return self._fallback_roadmap(missing_skills, target_role)

    async def _claude_generate(self, missing_skills: list, target_role: Optional[str], current_role: Optional[str], ats_score: float) -> dict:
        skills_str = ", ".join(missing_skills[:10]) if missing_skills else "general interview skills"

        prompt = f"""You are a career coach creating a personalized 30-day interview preparation roadmap.

Candidate Profile:
- Current Role: {current_role or "Software Engineer"}
- Target Role: {target_role or "Software Engineer"}
- Current ATS Score: {ats_score:.0f}/100
- Skills to Develop: {skills_str}

Create a detailed 4-week preparation plan. Return ONLY valid JSON (no markdown):
{{
  "weeks": [
    {{"week": 1, "focus": "Foundation Building", "topics": ["Topic 1", "Topic 2"], "resources": [{{"title": "Resource", "url": "https://...", "type": "course"}}], "projects": ["Build X"], "goals": ["Complete X"], "estimated_hours": 20}},
    {{"week": 2, "focus": "Core Skills Development", "topics": ["..."], "resources": [{{"title": "...", "url": "...", "type": "..."}}], "projects": ["..."], "goals": ["..."], "estimated_hours": 25}},
    {{"week": 3, "focus": "Advanced Topics & Projects", "topics": ["..."], "resources": [{{"title": "...", "url": "...", "type": "..."}}], "projects": ["..."], "goals": ["..."], "estimated_hours": 25}},
    {{"week": 4, "focus": "Interview Practice & Polish", "topics": ["..."], "resources": [{{"title": "...", "url": "...", "type": "..."}}], "projects": ["..."], "goals": ["..."], "estimated_hours": 20}}
  ],
  "milestones": [
    {{"day": 7, "milestone": "Complete Week 1 goals", "check": "Can explain basics"}},
    {{"day": 30, "milestone": "Interview ready", "check": "Mock interview score above 7/10"}}
  ],
  "resources": [{{"title": "LeetCode", "url": "https://leetcode.com", "type": "practice", "description": "Algorithm practice"}}]
}}"""

        client = self._get_client()
        response = await asyncio.get_event_loop().run_in_executor(None, lambda: client.messages.create(model="claude-sonnet-4-6", max_tokens=3000, messages=[{"role": "user", "content": prompt}]))
        text = response.content[0].text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError("Could not parse roadmap JSON")

    def _fallback_roadmap(self, missing_skills: list, target_role: Optional[str]) -> dict:
        skills_w1 = missing_skills[:2] if missing_skills else ["Data Structures", "Algorithms"]
        skills_w2 = missing_skills[2:4] if len(missing_skills) > 2 else ["System Design", "OOP Principles"]
        skills_w3 = missing_skills[4:6] if len(missing_skills) > 4 else ["API Development", "Database Design"]

        return {
            "weeks": [
                {"week": 1, "focus": f"Foundation: {', '.join(skills_w1)}", "topics": skills_w1 + ["Data Structures", "Time & Space Complexity"],
                 "resources": [{"title": "LeetCode Easy Problems", "url": "https://leetcode.com/problemset/?difficulty=EASY", "type": "practice"}, {"title": "freeCodeCamp", "url": "https://www.freecodecamp.org", "type": "course"}],
                 "projects": [f"Build a simple CRUD API using {skills_w1[0] if skills_w1 else 'Python'}", "Solve 5 LeetCode easy problems daily"],
                 "goals": ["Understand core concepts", "Complete 35 LeetCode problems", "Build one small project"], "estimated_hours": 20},
                {"week": 2, "focus": f"Core Skills: {', '.join(skills_w2)}", "topics": skills_w2 + ["Design Patterns", "REST APIs"],
                 "resources": [{"title": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer", "type": "book"}, {"title": "LeetCode Medium", "url": "https://leetcode.com/problemset/?difficulty=MEDIUM", "type": "practice"}],
                 "projects": ["Design and build a RESTful API with authentication", "Implement common design patterns"],
                 "goals": ["Master system design fundamentals", "Solve 35 medium problems"], "estimated_hours": 25},
                {"week": 3, "focus": f"Advanced Topics: {', '.join(skills_w3)}", "topics": skills_w3 + ["Cloud Deployment", "Performance Optimization"],
                 "resources": [{"title": "AWS Free Tier", "url": "https://aws.amazon.com/free", "type": "practice"}, {"title": "Docker Documentation", "url": "https://docs.docker.com", "type": "docs"}],
                 "projects": ["Deploy a project to cloud", "Containerize an application with Docker"],
                 "goals": ["Complete a production-ready project", "Learn cloud deployment basics"], "estimated_hours": 25},
                {"week": 4, "focus": "Interview Polish & Mock Practice", "topics": ["Behavioral Questions (STAR Method)", "Mock Interviews", "Resume Review"],
                 "resources": [{"title": "Pramp - Free Mock Interviews", "url": "https://www.pramp.com", "type": "practice"}, {"title": "Glassdoor Interview Questions", "url": "https://www.glassdoor.com/Interview", "type": "practice"}],
                 "projects": ["Record yourself answering common questions", "Do 3+ mock interviews"],
                 "goals": ["Score 7+ on mock interviews", "Prepare top 20 behavioral answers"], "estimated_hours": 20},
            ],
            "milestones": [
                {"day": 7, "milestone": "Foundation complete", "check": "Can code basic algorithms and explain core concepts"},
                {"day": 14, "milestone": "Portfolio project done", "check": "Built and deployed a working application"},
                {"day": 21, "milestone": "Advanced skills acquired", "check": "Comfortable with cloud and system design"},
                {"day": 30, "milestone": "Interview ready", "check": "Consistently scoring 7+/10 in mock interviews"},
            ],
            "resources": [
                {"title": "LeetCode", "url": "https://leetcode.com", "type": "practice", "description": "Algorithm & data structure problems"},
                {"title": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer", "type": "book", "description": "System design concepts"},
                {"title": "Tech Interview Handbook", "url": "https://www.techinterviewhandbook.org", "type": "guide", "description": "Comprehensive interview guide"},
                {"title": "Pramp", "url": "https://www.pramp.com", "type": "practice", "description": "Free peer mock interviews"},
            ],
        }


roadmap_generator = RoadmapGenerator()
