"""Code challenges (CODE CHALLENGE MODE): pick a topic, choose one challenge of
the several offered, solve it on your own and submit the resulting value.

The server compares the submitted value to the expected answer — no user code is
executed — and grants +100 XP the first time each challenge is solved (idempotent
via ChallengeProgress).
"""
import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .auth import get_current_user
from .db import get_session
from .models import Challenge, ChallengeProgress, Subcategory, Technology, User
from .xp import award_xp

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


class SubmitIn(BaseModel):
    challenge_id: int
    answer: str


def _norm_text(s: str) -> str:
    """Case-insensitive, whitespace-collapsed form for comparing text answers."""
    return re.sub(r"\s+", " ", (s or "").strip().casefold())


def _check(challenge: Challenge, given: str) -> bool:
    """Compare a submitted answer to the expected one (no code execution).

    'number' answers are compared numerically (accepts ',' as a decimal point);
    'text' answers are compared case-insensitively after collapsing whitespace.
    Several accepted answers may be stored separated by '|'.
    """
    given = (given or "").strip()
    if not given:
        return False
    accepted = [p.strip() for p in challenge.answer.split("|") if p.strip()]
    if challenge.answer_kind == "number":
        try:
            g = float(given.replace(",", "."))
        except ValueError:
            return False
        for part in accepted:
            try:
                if abs(g - float(part.replace(",", "."))) < 1e-9:
                    return True
            except ValueError:
                continue
        return False
    gn = _norm_text(given)
    return any(gn == _norm_text(p) for p in accepted)


@router.get("/topics")
async def challenge_topics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Technologies that have challenges, with total + how many the user solved."""
    counts = (
        await db.execute(
            select(Challenge.technology_id, func.count(Challenge.id)).group_by(
                Challenge.technology_id
            )
        )
    ).all()
    if not counts:
        return []
    count_map = dict(counts)

    solved = (
        await db.execute(
            select(Challenge.technology_id, func.count(ChallengeProgress.id))
            .join(ChallengeProgress, ChallengeProgress.challenge_id == Challenge.id)
            .where(ChallengeProgress.user_id == user.id)
            .group_by(Challenge.technology_id)
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


@router.get("/topics/{technology_id}")
async def challenge_list(
    technology_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Challenges of a topic (the '3 to choose from' synopses). No answers leaked."""
    challenges = (
        await db.scalars(
            select(Challenge)
            .where(Challenge.technology_id == technology_id)
            .order_by(Challenge.position, Challenge.id)
        )
    ).all()
    solved = set(
        (
            await db.scalars(
                select(ChallengeProgress.challenge_id).where(
                    ChallengeProgress.user_id == user.id
                )
            )
        ).all()
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "difficulty": c.difficulty,
            "prompt": c.prompt,
            "sample_input": c.sample_input,
            "starter_code": c.starter_code,
            "hint": c.hint,
            "answer_kind": c.answer_kind,
            "solved": c.id in solved,
        }
        for c in challenges
    ]


@router.post("/submit")
async def challenge_submit(
    payload: SubmitIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Check a submitted answer; award +100 XP the first time it's solved."""
    c = await db.get(Challenge, payload.challenge_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")

    correct = _check(c, payload.answer)
    awarded = 0
    leveled_up = False

    if correct:
        existing = await db.scalar(
            select(ChallengeProgress.id).where(
                ChallengeProgress.user_id == user.id,
                ChallengeProgress.challenge_id == c.id,
            )
        )
        if not existing:  # first correct solve → grant XP once
            db.add(ChallengeProgress(user_id=user.id, challenge_id=c.id))
            res = award_xp(user, "challenge")
            try:
                await db.commit()
                awarded = res["awarded"]
                leveled_up = res["leveled_up"]
            except IntegrityError:
                await db.rollback()  # rare race: solved concurrently
                user = await db.get(User, user.id)

    return {
        "correct": correct,
        # Explanation is revealed only once the challenge is solved.
        "explanation": c.explanation if correct else "",
        "awarded": awarded,
        "leveled_up": leveled_up,
        "xp": user.xp,
        "level": user.level,
    }
