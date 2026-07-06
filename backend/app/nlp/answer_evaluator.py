import json
import logging
import asyncio
from typing import Optional
import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


class AnswerEvaluator:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if not self._client:
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    async def evaluate(self, question: str, answer: str, question_type: str = "technical", expected_points: Optional[list] = None) -> dict:
        if not answer or len(answer.strip()) < 5:
            return self._empty_answer_response()
        try:
            return await self._claude_evaluate(question, answer, question_type, expected_points)
        except Exception as e:
            logger.error(f"Claude evaluation failed: {e}")
            return self._fallback_evaluate(answer, expected_points)

    async def _claude_evaluate(self, question: str, answer: str, question_type: str, expected_points: Optional[list]) -> dict:
        expected_str = ""
        if expected_points:
            expected_str = "\nKey points a good answer should cover:\n" + "\n".join(f"- {p}" for p in expected_points)

        prompt = f"""You are an expert technical interviewer evaluating a candidate's interview answer.

Question Type: {question_type}
Question: {question}{expected_str}

Candidate's Answer:
{answer[:3000]}

Evaluate the answer on these 4 dimensions (score each 0.0-10.0):
1. Relevance: How directly does the answer address the question?
2. Technical Accuracy: Is the technical content correct?
3. Completeness: Does the answer cover all key points?
4. Communication: Is the answer clear, structured, and easy to follow?

Also list keywords used/missed, 2-4 improvement suggestions, and a brief model answer.

Return ONLY valid JSON (no markdown):
{{
  "relevance_score": 7.5, "technical_accuracy_score": 6.0, "completeness_score": 7.0, "communication_score": 8.0,
  "overall_score": 7.1, "feedback": "Brief overall feedback sentence",
  "keywords_used": ["keyword1"], "keywords_missed": ["missed1"],
  "improvement_suggestions": ["Suggestion 1", "Suggestion 2"],
  "model_answer": "A strong answer would include..."
}}"""

        client = self._get_client()
        response = await asyncio.get_event_loop().run_in_executor(None, lambda: client.messages.create(model="claude-sonnet-4-6", max_tokens=1000, messages=[{"role": "user", "content": prompt}]))
        text = response.content[0].text.strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                raise ValueError("Could not parse JSON from Claude response")

        for field in ["relevance_score", "technical_accuracy_score", "completeness_score", "communication_score"]:
            result[field] = max(0.0, min(10.0, float(result.get(field, 5.0))))

        scores = [result["relevance_score"], result["technical_accuracy_score"], result["completeness_score"], result["communication_score"]]
        weights = [0.25, 0.35, 0.25, 0.15]
        result["overall_score"] = round(sum(s * w for s, w in zip(scores, weights)), 1)

        result.setdefault("keywords_used", [])
        result.setdefault("keywords_missed", [])
        result.setdefault("improvement_suggestions", [])
        return result

    def _fallback_evaluate(self, answer: str, expected_points: Optional[list]) -> dict:
        word_count = len(answer.split())
        length_score = min(10.0, max(2.0, word_count / 20))

        completeness = 5.0
        matched_points = []
        missed_points = []
        if expected_points:
            for point in expected_points:
                if any(word.lower() in answer.lower() for word in point.split()[:3]):
                    matched_points.append(point)
                else:
                    missed_points.append(point)
            completeness = (len(matched_points) / len(expected_points)) * 10

        sentences = answer.split(".")
        comm_score = min(10.0, max(3.0, len([s for s in sentences if len(s.strip()) > 10]) * 1.5))
        overall = round((length_score * 0.25 + completeness * 0.35 + comm_score * 0.25 + 5.0 * 0.15), 1)

        if word_count < 30:
            feedback = "Your answer is quite brief. Try to elaborate more with specific examples."
        elif word_count > 300:
            feedback = "Good detailed answer. Try to be more concise and structure your response clearly."
        else:
            feedback = "Decent answer length. Focus on covering the key technical concepts."

        return {
            "relevance_score": round(length_score, 1), "technical_accuracy_score": round(completeness, 1),
            "completeness_score": round(completeness, 1), "communication_score": round(comm_score, 1),
            "overall_score": overall, "feedback": feedback, "keywords_used": matched_points[:5], "keywords_missed": missed_points[:5],
            "improvement_suggestions": [
                "Provide specific examples from your experience to support your points.",
                "Use the STAR method (Situation, Task, Action, Result) for behavioral questions.",
                "Include technical terminology relevant to the question.",
            ][:3],
            "model_answer": None,
        }

    def _empty_answer_response(self) -> dict:
        return {
            "relevance_score": 0.0, "technical_accuracy_score": 0.0, "completeness_score": 0.0, "communication_score": 0.0,
            "overall_score": 0.0, "feedback": "No answer was provided for this question.",
            "keywords_used": [], "keywords_missed": [], "improvement_suggestions": ["Please provide a detailed answer to receive evaluation."], "model_answer": None,
        }


answer_evaluator = AnswerEvaluator()
