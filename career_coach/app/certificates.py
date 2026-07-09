"""Сертификаты («Сертификаты», Этап 6): награда за завершение курса и уровни-вехи.

Выдаются лениво: при заходе на страницу `GET /api/certificates` бэкенд заново
оценивает заслуги пользователя и создаёт недостающие записи. Ничего не начисляет
повторно — уникальность (user_id, kind, ref_id) гарантирует один сертификат на
одно достижение, а `created_at` фиксирует дату выдачи.

Виды (config.CERT_*):
  * 'course' — все уроки курса отмечены пройденными; ref_id = id курса.
  * 'level'  — достигнут уровень-веха (5/10/25/50); ref_id = уровень.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_user
from .config import CERT_LEVELS, CERT_RANKS
from .db import get_session
from .models import Certificate, Course, Lesson, LessonProgress, User

router = APIRouter(prefix="/api/certificates", tags=["certificates"])


async def _completed_course_ids(user_id: int, db: AsyncSession) -> list[int]:
    """Курсы, у которых пользователь прошёл ВСЕ уроки (и уроков хотя бы один)."""
    totals = dict(
        (
            await db.execute(
                select(Lesson.course_id, func.count(Lesson.id)).group_by(Lesson.course_id)
            )
        ).all()
    )
    done = dict(
        (
            await db.execute(
                select(Lesson.course_id, func.count(LessonProgress.id))
                .join(LessonProgress, LessonProgress.lesson_id == Lesson.id)
                .where(LessonProgress.user_id == user_id)
                .group_by(Lesson.course_id)
            )
        ).all()
    )
    return [cid for cid, total in totals.items() if total > 0 and done.get(cid, 0) >= total]


async def _issue_missing(user: User, db: AsyncSession) -> None:
    """Создать сертификаты за все текущие заслуги, которых ещё нет в БД."""
    existing = set(
        (
            await db.execute(
                select(Certificate.kind, Certificate.ref_id).where(
                    Certificate.user_id == user.id
                )
            )
        ).all()
    )

    new_rows: list[Certificate] = []

    # За завершённые курсы — снимок названия курса на момент выдачи.
    course_ids = await _completed_course_ids(user.id, db)
    missing_courses = [cid for cid in course_ids if ("course", cid) not in existing]
    if missing_courses:
        titles = dict(
            (
                await db.execute(
                    select(Course.id, Course.title).where(Course.id.in_(missing_courses))
                )
            ).all()
        )
        for cid in missing_courses:
            new_rows.append(
                Certificate(
                    user_id=user.id, kind="course", ref_id=cid,
                    title=titles.get(cid, "Курс"),
                )
            )

    # За достигнутые уровни-вехи — название ранга.
    for level in CERT_LEVELS:
        if user.level >= level and ("level", level) not in existing:
            new_rows.append(
                Certificate(
                    user_id=user.id, kind="level", ref_id=level,
                    title=CERT_RANKS.get(level, f"Уровень {level}"),
                )
            )

    if not new_rows:
        return
    db.add_all(new_rows)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()  # редкая гонка: выдано параллельным запросом


def _to_dict(cert: Certificate) -> dict:
    """Представление сертификата для фронта (номер, подпись под заголовком)."""
    if cert.kind == "level":
        subtitle = f"Достигнут уровень {cert.ref_id}"
    else:
        subtitle = "Курс пройден полностью"
    return {
        "id": cert.id,
        "kind": cert.kind,
        "ref_id": cert.ref_id,
        "title": cert.title,
        "subtitle": subtitle,
        "number": f"DUCKIE-{cert.id:04d}",
        "issued_at": cert.created_at.isoformat() if cert.created_at else None,
    }


@router.get("")
async def list_certificates(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Выдать недостающие сертификаты и вернуть все — новые первыми."""
    await _issue_missing(user, db)
    certs = (
        await db.scalars(
            select(Certificate)
            .where(Certificate.user_id == user.id)
            .order_by(Certificate.created_at.desc(), Certificate.id.desc())
        )
    ).all()
    return {
        "recipient": user.full_name or user.name,
        "certificates": [_to_dict(c) for c in certs],
    }
