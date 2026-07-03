"""ORM models."""
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Role-based access: 'user' (learner) | 'mentor' (adds courses, helps) | 'admin'.
    # is_admin is kept in sync (admin role) for backward compatibility.
    role: Mapped[str] = mapped_column(String(20), default="user", server_default="user", nullable=False)
    # Заявка на роль ментора: None (нет) | "pending" (на рассмотрении) | "rejected".
    # При одобрении админом role становится 'mentor', а заявка очищается.
    mentor_request: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mentor_request_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    # what the user is learning now (category slug); null until they pick one
    direction: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # directions the user plans to learn next (list of category slugs)
    planned: Mapped[list] = mapped_column(JSON, default=list, server_default="[]", nullable=False)
    # personal info (filled in from the "Информация" section)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    # URL path to the uploaded avatar (e.g. /static/uploads/avatars/3.png)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # chosen technology + course within the goal subcategory (null until picked)
    goal_technology_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goal_course_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # gamification (from docs.md): starts at level 0 / 0 XP
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    icon: Mapped[str] = mapped_column(String(16), default="📚", nullable=False)
    color: Mapped[str] = mapped_column(String(9), default="#5d3fd3", nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subcategories: Mapped[list["Subcategory"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="Subcategory.position",
    )


class Subcategory(Base):
    __tablename__ = "subcategories"
    __table_args__ = (UniqueConstraint("category_id", "slug", name="uq_subcat_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category: Mapped["Category"] = relationship(back_populates="subcategories")
    technologies: Mapped[list["Technology"]] = relationship(
        back_populates="subcategory",
        cascade="all, delete-orphan",
        order_by="Technology.position",
    )


class Technology(Base):
    """Concrete tool/framework under a subcategory, e.g. FastAPI under Python."""

    __tablename__ = "technologies"
    __table_args__ = (UniqueConstraint("subcategory_id", "slug", name="uq_tech_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subcategory_id: Mapped[int] = mapped_column(
        ForeignKey("subcategories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subcategory: Mapped["Subcategory"] = relationship(back_populates="technologies")
    courses: Mapped[list["Course"]] = relationship(
        back_populates="technology",
        cascade="all, delete-orphan",
        order_by="Course.position",
    )


class Course(Base):
    """A specific video course for a technology, by a given author."""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    technology_id: Mapped[int] = mapped_column(
        ForeignKey("technologies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    author: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    # human-readable length, e.g. "12 ч"; free-form so seeds stay simple
    duration: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    # aggregate rating shown in the UI; review texts live in the reviews table
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    technology: Mapped["Technology"] = relationship(back_populates="courses")
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Review.position",
    )
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Lesson.position",
    )


class Lesson(Base):
    """A single step of a course's learning plan (план обучения)."""

    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(400), default="", nullable=False)
    duration: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # YouTube video for the lesson: 11-char video id + optional start offset (sec),
    # so several lessons can be "chapters" of one long course video.
    youtube_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    video_start: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    course: Mapped["Course"] = relationship(back_populates="lessons")


class Review(Base):
    """A short review left by someone who took a course."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    author: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    rating: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    text: Mapped[str] = mapped_column(String(600), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    course: Mapped["Course"] = relationship(back_populates="reviews")


class Question(Base):
    """A quiz question tied to a technology (topic). Options live in a separate
    table (question_options); their display order is shuffled by the API."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    technology_id: Mapped[int] = mapped_column(
        ForeignKey("technologies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    options: Mapped[list["QuestionOption"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.position",
    )


class QuestionOption(Base):
    """An answer option for a question, with a per-option explanation."""

    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    text: Mapped[str] = mapped_column(String(300), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanation: Mapped[str] = mapped_column(String(400), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question: Mapped["Question"] = relationship(back_populates="options")


class QuizProgress(Base):
    """One row per question a user has answered correctly (idempotent XP).

    The row's existence means the +10 XP for that question was already granted.
    """

    __tablename__ = "quiz_progress"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_quiz_progress"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class QuizAttempt(Base):
    """A completed quiz run for one topic (technology): score + percent + when.

    Kept as history so the user can see whether their knowledge is trending up or
    down over repeated attempts. Unlike QuizProgress (per-question, idempotent XP),
    every finished test appends a new row here.
    """

    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    technology_id: Mapped[int] = mapped_column(
        ForeignKey("technologies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    correct: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    percent: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LessonProgress(Base):
    """One row per lesson a user has marked completed («урок пройден»).

    The row's existence means the lesson is done; used for the «Пройденные уроки»
    list and per-course progress. No XP is tied to it (XP comes from quiz/challenge).
    """

    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Challenge(Base):
    """A code challenge tied to a technology (CODE CHALLENGE MODE).

    The user solves it on their own (there's a scratch code area that is not
    checked) and submits the resulting value. The server compares that value to
    the expected answer — no code is executed — and grants +100 XP on the first
    correct submit (see ChallengeProgress).
    """

    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    technology_id: Mapped[int] = mapped_column(
        ForeignKey("technologies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    # 'easy' | 'medium' | 'hard' — surfaced as a coloured label in the UI.
    difficulty: Mapped[str] = mapped_column(String(20), default="easy", nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    sample_input: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    # Optional starter code shown in the (unchecked) scratch editor.
    starter_code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    hint: Mapped[str] = mapped_column(String(400), default="", nullable=False)
    # Expected answer + how to compare it. answer_kind: 'number' | 'text'.
    # Several accepted answers may be separated by '|'.
    answer: Mapped[str] = mapped_column(String(300), nullable=False)
    answer_kind: Mapped[str] = mapped_column(String(10), default="number", nullable=False)
    explanation: Mapped[str] = mapped_column(String(600), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ChallengeProgress(Base):
    """One row per challenge a user has solved (idempotent +100 XP).

    The row's existence means the +100 XP for that challenge was already granted.
    """

    __tablename__ = "challenge_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="uq_challenge_progress"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
