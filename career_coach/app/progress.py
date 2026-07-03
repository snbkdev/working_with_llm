"""Lesson progress (LEARNING MODE, шаг «урок пройден»).

Tracks which lessons a user has completed, powering the «Пройденные уроки» list
and per-course progress bars. No XP is granted here — XP comes from quizzes and
challenges; completing a lesson is a personal checkmark.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_user
from .db import get_session
from .models import Course, Lesson, LessonProgress, User

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.post("/lessons/{lesson_id}")
async def mark_lesson_done(
    lesson_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Mark a lesson completed (idempotent)."""
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Урок не найден")
    existing = await db.scalar(
        select(LessonProgress.id).where(
            LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id
        )
    )
    if not existing:
        db.add(LessonProgress(user_id=user.id, lesson_id=lesson_id))
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()  # rare race: already marked concurrently
    return {"completed": True}


@router.delete("/lessons/{lesson_id}")
async def unmark_lesson_done(
    lesson_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Remove the completed mark from a lesson (toggle off)."""
    existing = await db.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id
        )
    )
    if existing:
        await db.delete(existing)
        await db.commit()
    return {"completed": False}


@router.get("/lessons")
async def completed_lessons(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """All lessons the user has completed, newest first — for «Пройденные уроки»."""
    rows = (
        await db.execute(
            select(
                Lesson.id,
                Lesson.title,
                Course.id,
                Course.title,
                LessonProgress.created_at,
            )
            .join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .join(Course, Course.id == Lesson.course_id)
            .where(LessonProgress.user_id == user.id)
            .order_by(LessonProgress.created_at.desc())
        )
    ).all()
    return [
        {
            "lesson_id": lid,
            "lesson_title": ltitle,
            "course_id": cid,
            "course_title": ctitle,
        }
        for (lid, ltitle, cid, ctitle, _created) in rows
    ]


@router.get("/courses/{course_id}")
async def course_progress(
    course_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Per-course completion for the current user: total lessons, done, which ids."""
    total = await db.scalar(
        select(func.count()).select_from(Lesson).where(Lesson.course_id == course_id)
    )
    done_ids = (
        await db.scalars(
            select(LessonProgress.lesson_id)
            .join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .where(Lesson.course_id == course_id, LessonProgress.user_id == user.id)
        )
    ).all()
    return {
        "total": total or 0,
        "completed": len(done_ids),
        "completed_lesson_ids": list(done_ids),
    }
