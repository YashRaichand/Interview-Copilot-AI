import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AnswerScorer:
    """Heuristic quality scorer backed by Claude API evaluation in answer_evaluator.py."""

    def score(self, question: str, answer: str, context: Optional[str] = None) -> dict:
        if not answer or len(answer.strip()) < 5:
            return self._zero_scores()
        return self._heuristic_score(question, answer)

    def _heuristic_score(self, question: str, answer: str) -> dict:
        words = answer.split()
        word_count = len(words)
        sentence_count = len([s for s in answer.split(".") if s.strip()])

        if word_count < 20:
            length_score = 3.0
        elif word_count < 50:
            length_score = 5.0
        elif word_count <= 300:
            length_score = 8.0 + min(2.0, (word_count - 50) / 250 * 2)
        else:
            length_score = max(5.0, 10.0 - (word_count - 300) / 100)

        structure_score = min(10.0, sentence_count * 1.5)

        q_words = set(question.lower().split())
        a_words = set(answer.lower().split())
        overlap_ratio = len(q_words & a_words) / max(len(q_words), 1)
        relevance_score = min(10.0, overlap_ratio * 30 + 4)

        example_indicators = ["for example", "for instance", "such as", "like", "e.g.", "specifically", "in my experience"]
        example_bonus = 1.0 if any(ind in answer.lower() for ind in example_indicators) else 0.0

        overall = min(10.0, max(0.0, round((length_score * 0.25 + structure_score * 0.25 + relevance_score * 0.35 + 5 * 0.15) + example_bonus, 1)))

        return {
            "overall_score": overall, "length_score": round(length_score, 1), "structure_score": round(structure_score, 1),
            "relevance_score": round(relevance_score, 1), "word_count": word_count, "sentence_count": sentence_count,
        }

    def _zero_scores(self) -> dict:
        return {"overall_score": 0.0, "length_score": 0.0, "structure_score": 0.0, "relevance_score": 0.0, "word_count": 0, "sentence_count": 0}


answer_scorer = AnswerScorer()
