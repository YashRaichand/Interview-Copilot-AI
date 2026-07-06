from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# ─── JD Service ──────────────────────────────────────────────────────────────

class JDService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_jd(self, data, user_id: UUID):
        from app.models import JobDescription
        jd = JobDescription(user_id=user_id, title=data.title, company=data.company, raw_text=data.raw_text, source_type="text")
        self.db.add(jd)
        await self.db.flush()
        return jd

    async def upload_jd_pdf(self, file_data: bytes, filename: str, title: str, company: Optional[str], user_id: UUID):
        from app.models import JobDescription
        from app.utils.pdf_extractor import pdf_extractor
        from app.utils.cloudinary_client import cloudinary_client

        raw_text = pdf_extractor.extract_text(file_data)
        try:
            upload_result = await cloudinary_client.upload_jd(file_data, filename, str(user_id))
            url = upload_result["url"]
        except Exception:
            url = f"local://{filename}"

        jd = JobDescription(user_id=user_id, title=title or filename, company=company, raw_text=raw_text, source_type="pdf", cloudinary_url=url)
        self.db.add(jd)
        await self.db.flush()
        return jd

    async def parse_jd_background(self, jd_id: str):
        from app.database import AsyncSessionLocal
        from app.models import JobDescription
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(select(JobDescription).where(JobDescription.id == UUID(jd_id)))
                jd = result.scalar_one_or_none()
                if not jd:
                    return

                from app.nlp.jd_parser import jd_parser
                parsed = jd_parser.parse(jd.raw_text)

                jd.required_skills = parsed.get("required_skills", [])
                jd.preferred_skills = parsed.get("preferred_skills", [])
                jd.experience_required = parsed.get("experience_required")
                jd.education_required = parsed.get("education_required")
                jd.responsibilities = parsed.get("responsibilities", [])
                jd.employment_type = parsed.get("employment_type")
                jd.location = parsed.get("location")

                from app.nlp.semantic_matcher import semantic_matcher
                embedding = await semantic_matcher.encode(jd.raw_text)
                jd.embedding = embedding.tolist()
                jd.is_parsed = True

                await db.commit()
                logger.info(f"JD {jd_id} parsed successfully")
            except Exception as e:
                logger.error(f"JD parsing failed for {jd_id}: {e}")
                await db.rollback()


# ─── Analysis Service ─────────────────────────────────────────────────────────

class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_full_analysis(self, resume_id: UUID, jd_id: UUID, user_id: UUID):
        from app.models import Resume, JobDescription, Analysis
        from fastapi import HTTPException

        r = await self.db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id))
        resume = r.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        if not resume.is_parsed:
            raise HTTPException(status_code=400, detail="Resume is still being parsed. Please try again in a moment.")

        j = await self.db.execute(select(JobDescription).where(JobDescription.id == jd_id, JobDescription.user_id == user_id))
        jd = j.scalar_one_or_none()
        if not jd:
            raise HTTPException(status_code=404, detail="Job description not found")
        if not jd.is_parsed:
            raise HTTPException(status_code=400, detail="Job description is still being parsed. Please try again in a moment.")

        from app.nlp.ats_scorer import ats_scorer
        from app.nlp.skill_detector import skill_detector
        from app.nlp.semantic_matcher import semantic_matcher
        import numpy as np

        if resume.embedding and jd.embedding:
            r_emb = np.array(resume.embedding)
            j_emb = np.array(jd.embedding)
        else:
            r_emb = await semantic_matcher.encode(resume.raw_text or "")
            j_emb = await semantic_matcher.encode(jd.raw_text or "")
        semantic_sim = float(np.dot(r_emb, j_emb) / (np.linalg.norm(r_emb) * np.linalg.norm(j_emb) + 1e-9))

        resume_skills = []
        if resume.skills:
            for category_skills in resume.skills.values():
                if isinstance(category_skills, list):
                    resume_skills.extend(category_skills)

        jd_required = jd.required_skills or []
        jd_preferred = jd.preferred_skills or []
        all_jd_skills = list(set(jd_required + jd_preferred))

        missing, matching = skill_detector.detect_missing_skills(resume_skills, all_jd_skills, jd_required, jd_preferred)
        skill_match_pct = len(matching) / len(all_jd_skills) * 100 if all_jd_skills else 0

        score_data = ats_scorer.calculate_score(
            resume_text=resume.raw_text or "",
            jd_text=jd.raw_text or "",
            resume_skills=resume_skills,
            jd_skills=all_jd_skills,
            semantic_similarity=semantic_sim,
            resume_experience_years=resume.total_experience_years or 0,
            jd_experience_required=jd.experience_required or "",
        )

        success_prob = None
        try:
            from app.ml.success_predictor import success_predictor
            success_prob = success_predictor.predict(ats_score=score_data["ats_score"], skill_match=skill_match_pct)
        except Exception as e:
            logger.warning(f"Success prediction failed: {e}")

        analysis = Analysis(
            resume_id=resume_id,
            job_description_id=jd_id,
            ats_score=score_data["ats_score"],
            skill_match_percentage=skill_match_pct,
            semantic_similarity=semantic_sim * 100,
            keyword_match_score=score_data["keyword_score"],
            experience_match_score=score_data["experience_score"],
            score_breakdown=score_data["breakdown"],
            missing_skills=[m.model_dump() for m in missing],
            matching_skills=matching,
            recommendations=score_data.get("recommendations", []),
            success_probability=success_prob,
        )
        self.db.add(analysis)
        await self.db.flush()
        return analysis


# ─── Interview Service ────────────────────────────────────────────────────────

class InterviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_interview(self, data, user_id: UUID):
        from app.models import Interview, Question, Analysis
        from app.nlp.question_generator import question_generator

        job_role = None
        resume_text = None
        jd_text = None

        if data.analysis_id:
            r = await self.db.execute(select(Analysis).where(Analysis.id == data.analysis_id))
            analysis = r.scalar_one_or_none()
            if analysis:
                from app.models import Resume, JobDescription
                res = await self.db.execute(select(Resume).where(Resume.id == analysis.resume_id))
                resume = res.scalar_one_or_none()
                jd_res = await self.db.execute(select(JobDescription).where(JobDescription.id == analysis.job_description_id))
                jd = jd_res.scalar_one_or_none()
                if resume:
                    resume_text = resume.raw_text
                    job_role = resume.resume_category
                if jd:
                    jd_text = jd.raw_text

        interview = Interview(
            user_id=user_id, analysis_id=data.analysis_id, title=data.title or "Mock Interview",
            interview_type=data.interview_type, status="active", started_at=datetime.utcnow(),
        )
        self.db.add(interview)
        await self.db.flush()

        questions_data = await question_generator.generate(
            num_questions=data.num_questions, interview_type=data.interview_type,
            resume_text=resume_text, jd_text=jd_text, job_role=job_role,
        )

        for i, q in enumerate(questions_data):
            question = Question(
                interview_id=interview.id, question_text=q["question"], question_type=q["type"],
                difficulty=q.get("difficulty", "medium"), category=q.get("category"),
                expected_answer_points=q.get("key_points", []), order_index=i,
            )
            self.db.add(question)

        interview.total_questions = len(questions_data)
        await self.db.flush()
        return interview

    async def submit_and_evaluate_answer(self, interview_id: UUID, data, user_id: UUID):
        from app.models import Interview, Question, Answer
        from app.nlp.answer_evaluator import answer_evaluator
        from fastapi import HTTPException

        r = await self.db.execute(select(Interview).where(Interview.id == interview_id, Interview.user_id == user_id))
        interview = r.scalar_one_or_none()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        q = await self.db.execute(select(Question).where(Question.id == data.question_id, Question.interview_id == interview_id))
        question = q.scalar_one_or_none()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        evaluation = await answer_evaluator.evaluate(
            question=question.question_text, answer=data.answer_text,
            question_type=question.question_type, expected_points=question.expected_answer_points or [],
        )

        answer = Answer(
            question_id=question.id, answer_text=data.answer_text,
            relevance_score=evaluation["relevance_score"], technical_accuracy_score=evaluation["technical_accuracy_score"],
            completeness_score=evaluation["completeness_score"], communication_score=evaluation["communication_score"],
            overall_score=evaluation["overall_score"], feedback=evaluation["feedback"],
            improvement_suggestions=evaluation["improvement_suggestions"], model_answer=evaluation.get("model_answer"),
            keywords_used=evaluation.get("keywords_used", []), keywords_missed=evaluation.get("keywords_missed", []),
            time_taken_seconds=data.time_taken_seconds,
        )
        self.db.add(answer)
        interview.answered_questions += 1
        await self.db.flush()
        return answer

    async def complete_interview(self, interview_id: UUID, user_id: UUID):
        from app.models import Interview, Question
        from sqlalchemy.orm import selectinload
        from fastapi import HTTPException
        import numpy as np

        r = await self.db.execute(
            select(Interview).options(selectinload(Interview.questions).selectinload(Question.answer))
            .where(Interview.id == interview_id, Interview.user_id == user_id)
        )
        interview = r.scalar_one_or_none()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        answers = [q.answer for q in interview.questions if q.answer]
        if answers:
            overall_scores = [a.overall_score for a in answers if a.overall_score is not None]
            tech_scores = [a.technical_accuracy_score for a in answers if a.technical_accuracy_score is not None]
            comm_scores = [a.communication_score for a in answers if a.communication_score is not None]

            interview.overall_score = float(np.mean(overall_scores)) if overall_scores else None
            interview.technical_score = float(np.mean(tech_scores)) if tech_scores else None
            interview.communication_score = float(np.mean(comm_scores)) if comm_scores else None

            all_improvements = []
            for a in answers:
                if a.improvement_suggestions:
                    all_improvements.extend(a.improvement_suggestions)
            interview.improvement_areas = list(set(all_improvements))[:5]

        interview.status = "completed"
        interview.completed_at = datetime.utcnow()
        if interview.started_at:
            delta = datetime.utcnow() - interview.started_at
            interview.duration_minutes = int(delta.total_seconds() / 60)

        await self.db.flush()
        return interview

    async def process_chat_message(self, data, user_id: UUID):
        from app.models import Interview, Question, Answer
        from fastapi import HTTPException
        from app.schemas import MockInterviewResponse, AnswerSubmit, AnswerEvaluation, QuestionResponse

        r = await self.db.execute(select(Interview).where(Interview.id == data.interview_id, Interview.user_id == user_id))
        interview = r.scalar_one_or_none()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        if interview.status == "completed":
            return MockInterviewResponse(message="This interview has been completed. Start a new one to continue practicing!", is_complete=True, next_action="complete")

        if data.question_id:
            submit_data = AnswerSubmit(question_id=data.question_id, answer_text=data.message)
            answer = await self.submit_and_evaluate_answer(data.interview_id, submit_data, user_id)

            next_q = await self._get_next_question(interview.id, data.question_id)

            if not next_q:
                completed = await self.complete_interview(data.interview_id, user_id)
                return MockInterviewResponse(
                    message=f"Interview complete! Your overall score: {completed.overall_score:.1f}/10. Great work!",
                    is_complete=True, next_action="complete",
                )

            eval_schema = AnswerEvaluation(
                relevance_score=answer.relevance_score or 0, technical_accuracy_score=answer.technical_accuracy_score or 0,
                completeness_score=answer.completeness_score or 0, communication_score=answer.communication_score or 0,
                overall_score=answer.overall_score or 0, feedback=answer.feedback or "",
                improvement_suggestions=answer.improvement_suggestions or [], model_answer=answer.model_answer,
                keywords_used=answer.keywords_used or [], keywords_missed=answer.keywords_missed or [],
            )

            return MockInterviewResponse(
                message=f"Score: {answer.overall_score:.1f}/10 — {answer.feedback}",
                question=QuestionResponse.model_validate(next_q), evaluation=eval_schema,
                is_complete=False, next_action="answer",
            )

        first_q = await self._get_first_question(interview.id)
        if not first_q:
            return MockInterviewResponse(message="No questions available.", is_complete=True)

        return MockInterviewResponse(
            message="Welcome to your mock interview! Answer each question as you would in a real interview. Let's start!",
            question=QuestionResponse.model_validate(first_q), is_complete=False, next_action="answer",
        )

    async def _get_first_question(self, interview_id: UUID):
        from app.models import Question, Answer
        r = await self.db.execute(
            select(Question).outerjoin(Answer, Question.id == Answer.question_id)
            .where(Question.interview_id == interview_id, Answer.id == None)
            .order_by(Question.order_index).limit(1)
        )
        return r.scalar_one_or_none()

    async def _get_next_question(self, interview_id: UUID, current_question_id: UUID):
        from app.models import Question, Answer
        r = await self.db.execute(select(Question).where(Question.id == current_question_id))
        current = r.scalar_one_or_none()
        if not current:
            return None
        r2 = await self.db.execute(
            select(Question).outerjoin(Answer, Question.id == Answer.question_id)
            .where(Question.interview_id == interview_id, Question.order_index > current.order_index, Answer.id == None)
            .order_by(Question.order_index).limit(1)
        )
        return r2.scalar_one_or_none()


# ─── Roadmap Service ──────────────────────────────────────────────────────────

class RoadmapService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_roadmap(self, analysis_id: UUID, user_id: UUID):
        from app.models import Analysis, Roadmap, Resume, JobDescription
        from app.nlp.roadmap_generator import roadmap_generator
        from fastapi import HTTPException
        from sqlalchemy import update

        r = await self.db.execute(select(Analysis).where(Analysis.id == analysis_id))
        analysis = r.scalar_one_or_none()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        await self.db.execute(update(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True).values(is_active=False))

        res = await self.db.execute(select(Resume).where(Resume.id == analysis.resume_id))
        resume = res.scalar_one_or_none()
        jd_res = await self.db.execute(select(JobDescription).where(JobDescription.id == analysis.job_description_id))
        jd = jd_res.scalar_one_or_none()

        missing_skills = []
        if analysis.missing_skills:
            missing_skills = [s.get("skill") for s in analysis.missing_skills if s.get("skill")]

        plan = await roadmap_generator.generate(
            missing_skills=missing_skills, target_role=jd.title if jd else None,
            current_role=resume.resume_category if resume else None, ats_score=analysis.ats_score or 0,
        )

        roadmap = Roadmap(
            user_id=user_id, analysis_id=analysis_id,
            title=f"30-Day Prep: {jd.title if jd else 'Interview Preparation'}",
            target_role=jd.title if jd else None, target_company=jd.company if jd else None,
            duration_days=30, weeks=plan.get("weeks", []), skills_to_learn=missing_skills,
            resources=plan.get("resources", []), milestones=plan.get("milestones", []),
            progress_percentage=0.0, completed_items=[], is_active=True,
        )
        self.db.add(roadmap)
        await self.db.flush()
        return roadmap

    async def update_progress(self, roadmap_id: UUID, data, user_id: UUID):
        from app.models import Roadmap
        from fastapi import HTTPException

        r = await self.db.execute(select(Roadmap).where(Roadmap.id == roadmap_id, Roadmap.user_id == user_id))
        roadmap = r.scalar_one_or_none()
        if not roadmap:
            raise HTTPException(status_code=404, detail="Roadmap not found")

        completed = list(roadmap.completed_items or [])
        if data.is_completed and data.completed_item_id not in completed:
            completed.append(data.completed_item_id)
        elif not data.is_completed and data.completed_item_id in completed:
            completed.remove(data.completed_item_id)

        roadmap.completed_items = completed

        total_items = 0
        if roadmap.weeks:
            for week in roadmap.weeks:
                total_items += len(week.get("topics", []))
                total_items += len(week.get("projects", []))

        if total_items > 0:
            roadmap.progress_percentage = min(100.0, len(completed) / total_items * 100)

        await self.db.flush()
        return roadmap


# ─── Report Service ───────────────────────────────────────────────────────────

class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_report(self, data, user_id: UUID):
        from app.models import Report, Analysis, Interview

        title = f"Report - {datetime.utcnow().strftime('%Y-%m-%d')}"
        report_data = {}

        if data.analysis_id:
            r = await self.db.execute(select(Analysis).where(Analysis.id == data.analysis_id))
            analysis = r.scalar_one_or_none()
            if analysis:
                report_data["analysis"] = {
                    "ats_score": analysis.ats_score, "skill_match": analysis.skill_match_percentage,
                    "missing_skills": analysis.missing_skills, "recommendations": analysis.recommendations,
                }
                title = f"ATS Report - {datetime.utcnow().strftime('%Y-%m-%d')}"

        if data.interview_id:
            r = await self.db.execute(select(Interview).where(Interview.id == data.interview_id))
            interview = r.scalar_one_or_none()
            if interview:
                report_data["interview"] = {
                    "overall_score": interview.overall_score, "technical_score": interview.technical_score,
                    "communication_score": interview.communication_score, "feedback": interview.feedback_summary,
                }
                title = f"Interview Report - {datetime.utcnow().strftime('%Y-%m-%d')}"

        report = Report(user_id=user_id, analysis_id=data.analysis_id, interview_id=data.interview_id, report_type=data.report_type, title=title, report_data=report_data)
        self.db.add(report)
        await self.db.flush()
        return report


# ─── Dashboard Service ────────────────────────────────────────────────────────

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self, user_id: UUID):
        from app.models import Resume, Analysis, Interview, Roadmap
        from sqlalchemy import desc
        from app.schemas import DashboardStats, InterviewListItem, RoadmapResponse

        res_count = await self.db.execute(select(func.count(Resume.id)).where(Resume.user_id == user_id))
        analysis_count = await self.db.execute(select(func.count(Analysis.id)).join(Analysis.resume).where(Resume.user_id == user_id))
        interview_count = await self.db.execute(select(func.count(Interview.id)).where(Interview.user_id == user_id))

        scores_r = await self.db.execute(
            select(Analysis.ats_score, Analysis.created_at).join(Analysis.resume)
            .where(Resume.user_id == user_id, Analysis.ats_score != None)
            .order_by(Analysis.created_at.desc()).limit(10)
        )
        scores = scores_r.all()

        best_score = max((s[0] for s in scores), default=None)
        avg_score = sum(s[0] for s in scores) / len(scores) if scores else None
        latest_score = scores[0][0] if scores else None
        ats_trend = [{"date": str(s[1].date()), "score": s[0]} for s in reversed(scores)]

        recent_r = await self.db.execute(select(Interview).where(Interview.user_id == user_id).order_by(desc(Interview.created_at)).limit(5))
        recent_interviews = recent_r.scalars().all()

        active_r = await self.db.execute(select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True))
        active_roadmap = active_r.scalar_one_or_none()

        latest_analysis_r = await self.db.execute(
            select(Analysis).join(Analysis.resume).where(Resume.user_id == user_id).order_by(desc(Analysis.created_at)).limit(1)
        )
        latest_analysis = latest_analysis_r.scalar_one_or_none()
        missing_skills = []
        latest_skill_match = None
        success_prob = None

        if latest_analysis:
            if latest_analysis.missing_skills:
                missing_skills = [s.get("skill", "") for s in latest_analysis.missing_skills[:5]]
            latest_skill_match = latest_analysis.skill_match_percentage
            success_prob = latest_analysis.success_probability

        return DashboardStats(
            total_resumes=res_count.scalar() or 0, total_analyses=analysis_count.scalar() or 0,
            total_interviews=interview_count.scalar() or 0, best_ats_score=best_score,
            average_ats_score=round(avg_score, 1) if avg_score else None, latest_ats_score=latest_score,
            latest_skill_match=latest_skill_match, success_probability=success_prob,
            recent_interviews=[InterviewListItem.model_validate(i) for i in recent_interviews],
            ats_trend=ats_trend, missing_skills_summary=missing_skills,
            active_roadmap=RoadmapResponse.model_validate(active_roadmap) if active_roadmap else None,
        )
