"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("role", sa.Enum("user", "admin", "premium", name="userrole"), nullable=False, server_default="user"),
        sa.Column("auth_provider", sa.Enum("local", "google", name="authprovider"), nullable=False, server_default="local"),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("google_id", name="uq_users_google_id"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("cloudinary_url", sa.Text(), nullable=False),
        sa.Column("cloudinary_public_id", sa.String(255), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("candidate_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("linkedin_url", sa.Text(), nullable=True),
        sa.Column("github_url", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("skills", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("experience", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("education", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("projects", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("certifications", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("total_experience_years", sa.Float(), nullable=True),
        sa.Column("resume_category", sa.String(100), nullable=True),
        sa.Column("is_parsed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_resumes_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_resumes"),
    )

    op.create_table(
        "job_descriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False, server_default="text"),
        sa.Column("cloudinary_url", sa.Text(), nullable=True),
        sa.Column("required_skills", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("preferred_skills", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("experience_required", sa.String(100), nullable=True),
        sa.Column("education_required", sa.String(255), nullable=True),
        sa.Column("responsibilities", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("benefits", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("salary_range", sa.String(100), nullable=True),
        sa.Column("embedding", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_parsed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_job_descriptions_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_job_descriptions"),
    )

    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_description_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ats_score", sa.Float(), nullable=True),
        sa.Column("skill_match_percentage", sa.Float(), nullable=True),
        sa.Column("semantic_similarity", sa.Float(), nullable=True),
        sa.Column("keyword_match_score", sa.Float(), nullable=True),
        sa.Column("experience_match_score", sa.Float(), nullable=True),
        sa.Column("score_breakdown", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("missing_skills", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("matching_skills", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("recommendations", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("success_probability", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], name="fk_analyses_resume_id_resumes", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_description_id"], ["job_descriptions.id"], name="fk_analyses_jd_id_job_descriptions", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_analyses"),
    )

    op.create_table(
        "interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("interview_type", sa.String(50), nullable=False, server_default="mixed"),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("technical_score", sa.Float(), nullable=True),
        sa.Column("communication_score", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answered_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("feedback_summary", sa.Text(), nullable=True),
        sa.Column("improvement_areas", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("strengths", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_interviews_user_id_users", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], name="fk_interviews_analysis_id_analyses", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_interviews"),
    )

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(50), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("expected_answer_points", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_follow_up", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("parent_question_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], name="fk_questions_interview_id_interviews", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_question_id"], ["questions.id"], name="fk_questions_parent_id_questions"),
        sa.PrimaryKeyConstraint("id", name="pk_questions"),
    )

    op.create_table(
        "answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("technical_accuracy_score", sa.Float(), nullable=True),
        sa.Column("completeness_score", sa.Float(), nullable=True),
        sa.Column("communication_score", sa.Float(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("improvement_suggestions", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("model_answer", sa.Text(), nullable=True),
        sa.Column("keywords_used", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("keywords_missed", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("time_taken_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name="fk_answers_question_id_questions", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_answers"),
        sa.UniqueConstraint("question_id", name="uq_answers_question_id"),
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("cloudinary_url", sa.Text(), nullable=True),
        sa.Column("cloudinary_public_id", sa.String(255), nullable=True),
        sa.Column("report_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_reports_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_reports"),
    )

    op.create_table(
        "roadmaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("target_role", sa.String(255), nullable=True),
        sa.Column("target_company", sa.String(255), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("weeks", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("skills_to_learn", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("resources", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("milestones", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("progress_percentage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("completed_items", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_roadmaps_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_roadmaps"),
    )

    op.create_table(
        "analytics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_analytics_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_analytics"),
    )
    op.create_index("ix_analytics_event_type", "analytics", ["event_type"])
    op.create_index("ix_analytics_created_at", "analytics", ["created_at"])


def downgrade() -> None:
    op.drop_table("analytics")
    op.drop_table("roadmaps")
    op.drop_table("reports")
    op.drop_table("answers")
    op.drop_table("questions")
    op.drop_table("interviews")
    op.drop_table("analyses")
    op.drop_table("job_descriptions")
    op.drop_table("resumes")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS authprovider")
