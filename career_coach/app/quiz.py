"""Quiz (QUIZ MODE): questions by topic (technology), answering with per-option
explanations, and +10 XP for the first correct answer to each question.

Options live in a separate table and their display order is shuffled per request.
"""
import random

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .auth import get_current_user
from .db import get_session
from .models import Question, QuizProgress, Subcategory, Technology, User
from .xp import award_xp

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


class AnswerIn(BaseModel):
    question_id: int
    option_id: int


@router.get("/topics")
async def quiz_topics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Technologies that have questions, with total + how many the user solved."""
    counts = (
        await db.execute(
            select(Question.technology_id, func.count(Question.id)).group_by(
                Question.technology_id
            )
        )
    ).all()
    if not counts:
        return []
    count_map = dict(counts)

    solved = (
        await db.execute(
            select(Question.technology_id, func.count(QuizProgress.id))
            .join(QuizProgress, QuizProgress.question_id == Question.id)
            .where(QuizProgress.user_id == user.id)
            .group_by(Question.technology_id)
        )
    ).all()
    solved_map = dict(solved)

    techs = (
        await db.scalars(
            select(Technology)
            .where(Technology.id.in_(count_map.keys()))
            .options(selectinload(Technology.subcategory).selectinload(Subcategory.category))
        )
    ).all()

    out = []
    for t in techs:
        sub = t.subcategory
        cat = sub.category if sub else None
        out.append({
            "technology_id": t.id,
            "title": t.title,
            "subcategory": sub.title if sub else None,
            "category": cat.title if cat else None,
            "color": cat.color if cat else None,
            "total": count_map.get(t.id, 0),
            "solved": solved_map.get(t.id, 0),
        })
    out.sort(key=lambda x: (x["category"] or "", x["title"]))
    return out


@router.get("/topics/{technology_id}/questions")
async def quiz_questions(
    technology_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Questions of a topic with options in shuffled order (no answers leaked)."""
    questions = (
        await db.scalars(
            select(Question)
            .where(Question.technology_id == technology_id)
            .options(selectinload(Question.options))
            .order_by(Question.position, Question.id)
        )
    ).all()
    solved = set(
        (
            await db.scalars(
                select(QuizProgress.question_id).where(QuizProgress.user_id == user.id)
            )
        ).all()
    )

    result = []
    for q in questions:
        opts = list(q.options)
        random.shuffle(opts)  # перемешиваем порядок вариантов при выводе
        result.append({
            "id": q.id,
            "text": q.text,
            "solved": q.id in solved,
            "options": [{"id": o.id, "text": o.text} for o in opts],
        })
    return result


@router.post("/answer")
async def quiz_answer(
    payload: AnswerIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Check an answer; award +10 XP the first time a question is solved."""
    q = await db.scalar(
        select(Question)
        .where(Question.id == payload.question_id)
        .options(selectinload(Question.options))
    )
    if not q:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Вопрос не найден")
    chosen = next((o for o in q.options if o.id == payload.option_id), None)
    if chosen is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Вариант не найден")

    correct_opt = next((o for o in q.options if o.is_correct), None)
    is_correct = chosen.is_correct
    awarded = 0
    leveled_up = False

    if is_correct:
        existing = await db.scalar(
            select(QuizProgress.id).where(
                QuizProgress.user_id == user.id, QuizProgress.question_id == q.id
            )
        )
        if not existing:  # first correct solve → grant XP once
            db.add(QuizProgress(user_id=user.id, question_id=q.id))
            res = award_xp(user, "quiz")
            try:
                await db.commit()
                awarded = res["awarded"]
                leveled_up = res["leveled_up"]
            except IntegrityError:
                await db.rollback()  # rare race: solved concurrently
                user = await db.get(User, user.id)

    return {
        "correct": is_correct,
        "correct_option_id": correct_opt.id if correct_opt else None,
        # keys become strings in JSON — the frontend looks them up by String(id)
        "explanations": {o.id: o.explanation for o in q.options if o.explanation},
        "awarded": awarded,
        "leveled_up": leveled_up,
        "xp": user.xp,
        "level": user.level,
    }
