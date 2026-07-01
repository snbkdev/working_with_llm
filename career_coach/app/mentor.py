"""Mentor tools: add courses (with YouTube-link lessons).

Available to mentors and admins. Course info is short (title, author, description);
each lesson plays a YouTube video parsed from a link.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import require_mentor
from .db import get_session
from .models import Course, Lesson, Technology
from .youtube import parse_youtube

router = APIRouter(prefix="/api/mentor", tags=["mentor"], dependencies=[Depends(require_mentor)])


class LessonIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=1, max_length=500)


class CourseIn(BaseModel):
    technology_id: int
    title: str = Field(min_length=1, max_length=160)
    author: str = Field(default="", max_length=120)
    duration: str = Field(default="", max_length=40)
    description: str = Field(default="", max_length=255)
    lessons: list[LessonIn] = Field(min_length=1)


@router.post("/courses", status_code=status.HTTP_201_CREATED)
async def create_course(payload: CourseIn, db: AsyncSession = Depends(get_session)) -> dict:
    """Create a course under a technology; each lesson's YouTube link is parsed
    into a video id + start offset. Rejects the request if no lesson has a
    recognisable YouTube link."""
    tech = await db.get(Technology, payload.technology_id)
    if not tech:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Технология не найдена")

    parsed: list[tuple[LessonIn, str, int]] = []
    for lesson in payload.lessons:
        vid, start = parse_youtube(lesson.url)
        if vid:
            parsed.append((lesson, vid, start))
    if not parsed:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Ни одна ссылка не распознана как YouTube-видео",
        )

    count = await db.scalar(
        select(func.count()).select_from(Course).where(Course.technology_id == tech.id)
    )
    course = Course(
        technology_id=tech.id,
        title=payload.title, author=payload.author,
        duration=payload.duration, description=payload.description,
        url=f"https://youtu.be/{parsed[0][1]}", position=count,
    )
    for pos, (lesson, vid, start) in enumerate(parsed):
        course.lessons.append(
            Lesson(
                title=lesson.title, position=pos,
                youtube_id=vid, video_start=start,
            )
        )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return {
        "id": course.id,
        "title": course.title,
        "lessons_added": len(parsed),
        "lessons_skipped": len(payload.lessons) - len(parsed),
    }
