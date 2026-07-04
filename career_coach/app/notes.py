"""Study notes («Заметки по курсам»): personal notes, optionally tied to a course.

Each user manages their own notes (create / edit / delete). A note may be attached
to a course or kept general (course_id = null).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_user
from .db import get_session
from .models import Course, Note, User

router = APIRouter(prefix="/api/notes", tags=["notes"])


class NoteIn(BaseModel):
    title: str = Field(default="", max_length=200)
    body: str = ""
    course_id: int | None = None


class NotePatch(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    body: str | None = None
    course_id: int | None = None


async def _note_dict(note: Note, db: AsyncSession) -> dict:
    ctitle = None
    if note.course_id:
        course = await db.get(Course, note.course_id)
        ctitle = course.title if course else None
    return {
        "id": note.id,
        "title": note.title,
        "body": note.body,
        "course_id": note.course_id,
        "course_title": ctitle,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
    }


async def _validate_course(course_id: int | None, db: AsyncSession) -> None:
    if course_id is not None and not await db.get(Course, course_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Курс не найден")


@router.get("")
async def list_notes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """All notes of the current user, most recently updated first."""
    rows = (
        await db.execute(
            select(Note, Course.title)
            .outerjoin(Course, Course.id == Note.course_id)
            .where(Note.user_id == user.id)
            .order_by(Note.updated_at.desc())
        )
    ).all()
    return [
        {
            "id": note.id,
            "title": note.title,
            "body": note.body,
            "course_id": note.course_id,
            "course_title": ctitle,
            "updated_at": note.updated_at.isoformat() if note.updated_at else None,
        }
        for note, ctitle in rows
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    if not payload.title.strip() and not payload.body.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Заметка не может быть пустой")
    await _validate_course(payload.course_id, db)
    note = Note(
        user_id=user.id,
        title=payload.title.strip(),
        body=payload.body,
        course_id=payload.course_id,
    )
    db.add(note)
    await db.commit()
    return await _note_dict(note, db)


@router.patch("/{note_id}")
async def update_note(
    note_id: int,
    payload: NotePatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    note = await db.get(Note, note_id)
    if not note or note.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заметка не найдена")
    data = payload.model_dump(exclude_unset=True)
    if "course_id" in data:
        await _validate_course(data["course_id"], db)
    if "title" in data and data["title"] is not None:
        data["title"] = data["title"].strip()
    for field, value in data.items():
        setattr(note, field, value)
    await db.commit()
    return await _note_dict(note, db)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> None:
    note = await db.get(Note, note_id)
    if not note or note.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заметка не найдена")
    await db.delete(note)
    await db.commit()
