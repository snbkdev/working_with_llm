"""Async SQLAlchemy engine, session factory and Base."""
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for ORM models."""


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async DB session."""
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables from model metadata (no migrations yet)."""
    # Import models so they register on Base.metadata before create_all.
    from sqlalchemy import text

    from . import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Lightweight column migrations for already-existing tables (no Alembic yet).
        for ddl in (
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS direction VARCHAR(50)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(200)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date DATE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS planned JSON DEFAULT '[]'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false NOT NULL",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS goal_technology_id INTEGER",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS goal_course_id INTEGER",
            "ALTER TABLE courses ADD COLUMN IF NOT EXISTS rating DOUBLE PRECISION DEFAULT 0 NOT NULL",
            "ALTER TABLE courses ADD COLUMN IF NOT EXISTS reviews_count INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS youtube_id VARCHAR(20)",
            "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS video_start INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user' NOT NULL",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS mentor_request VARCHAR(20)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS mentor_request_note TEXT",
            # Backfill: existing admins get the admin role.
            "UPDATE users SET role = 'admin' WHERE is_admin = true AND role <> 'admin'",
        ):
            await conn.execute(text(ddl))

    # Case-insensitive unique email at the DB level (defense in depth). Kept in a
    # separate, guarded transaction so legacy rows with case-duplicate emails
    # can't block startup — app-level normalization already prevents new dupes.
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_lower "
                    "ON users (lower(email))"
                )
            )
    except Exception:
        logging.getLogger("duckie").warning(
            "Не удалось создать уникальный индекс lower(email) — вероятно, есть дубли по регистру."
        )

    await seed_catalog()


async def seed_catalog() -> None:
    """Populate categories/subcategories from seed data if the table is empty,
    then backfill technologies/courses if those tables are empty."""
    from sqlalchemy import func, select

    from .models import Category, Subcategory
    from .seed import SEED_CATEGORIES

    async with SessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(Category))
        if not count:
            for pos, cat in enumerate(SEED_CATEGORIES):
                category = Category(
                    slug=cat["slug"], title=cat["title"], icon=cat["icon"],
                    color=cat["color"], description=cat["description"], position=pos,
                )
                for spos, sub in enumerate(cat["subcategories"]):
                    category.subcategories.append(
                        Subcategory(
                            slug=sub["slug"], title=sub["title"],
                            description=sub["description"], position=spos,
                        )
                    )
                session.add(category)
            await session.commit()

    await seed_tree()


async def seed_tree() -> None:
    """Backfill technologies and their courses for already-seeded subcategories.

    Incremental: adds any seed technology that does not yet exist under its
    subcategory (keyed by subcategory + slug), leaving existing rows untouched.
    Works on a fresh DB and on one that was seeded with an earlier, smaller set.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from .models import Category, Course, Subcategory, Technology
    from .seed import SEED_CATEGORIES

    async with SessionLocal() as session:
        # Map (category_slug, subcategory_slug) -> Subcategory, with existing
        # technology slugs preloaded so we can skip ones already present.
        cats = (
            await session.scalars(
                select(Category).options(
                    selectinload(Category.subcategories).selectinload(Subcategory.technologies)
                )
            )
        ).all()
        subs: dict[tuple[str, str], Subcategory] = {
            (cat.slug, sub.slug): sub for cat in cats for sub in cat.subcategories
        }

        added = False
        for cat in SEED_CATEGORIES:
            for sub in cat["subcategories"]:
                target = subs.get((cat["slug"], sub["slug"]))
                if target is None:
                    continue
                existing_slugs = {t.slug for t in target.technologies}
                base_pos = len(target.technologies)
                for offset, tech in enumerate(sub.get("technologies", [])):
                    if tech["slug"] in existing_slugs:
                        continue
                    technology = Technology(
                        subcategory_id=target.id, slug=tech["slug"],
                        title=tech["title"], description=tech["description"],
                        position=base_pos + offset,
                    )
                    for cpos, course in enumerate(tech.get("courses", [])):
                        technology.courses.append(
                            Course(
                                title=course["title"], author=course.get("author", ""),
                                duration=course.get("duration", ""), url=course.get("url", ""),
                                description=course.get("description", ""), position=cpos,
                            )
                        )
                    session.add(technology)
                    added = True
        if added:
            await session.commit()

    await seed_lessons()
    await seed_youtube_courses()
    await reconcile_video_courses()
    await seed_link_courses()
    await prune_courses_without_video()
    await seed_questions()
    await seed_challenges()
    # Reviews/ratings are intentionally left empty for now — real user reviews
    # will be added later as a separate feature.


# Generic but coherent learning-plan steps; {tech} is filled per course.
_LESSON_PLAN = [
    ("Введение и настройка окружения",
     "Знакомство с курсом, установка инструментов и первый запуск.", "1 ч"),
    ("Основы и базовый синтаксис",
     "Ключевые понятия и первые практические примеры.", "2 ч"),
    ("Главные концепции {tech}",
     "Разбираем основные возможности {tech} на практике.", "3 ч"),
    ("Работа с данными",
     "Структуры данных, ввод-вывод, обработка типичных задач.", "2 ч"),
    ("Практика: первое приложение",
     "Собираем небольшой проект, закрепляя пройденное.", "3 ч"),
    ("Продвинутые возможности {tech}",
     "Углубляемся в темы для уверенного уровня.", "3 ч"),
    ("Тестирование и отладка",
     "Находим и исправляем ошибки, пишем проверки.", "2 ч"),
    ("Итоговый проект",
     "Финальная работа, которая собирает все навыки воедино.", "4 ч"),
]


async def seed_lessons() -> None:
    """Backfill a learning plan (lessons) for any course that has none yet."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from .models import Course, Lesson, Technology

    async with SessionLocal() as session:
        courses = (
            await session.scalars(
                select(Course).options(
                    selectinload(Course.lessons), selectinload(Course.technology)
                )
            )
        ).all()
        added = False
        for course in courses:
            if course.lessons:  # already has a plan — leave as is
                continue
            tech = course.technology.title if course.technology else "технологию"
            # Drop a trailing "(основы …)" so substitutions read naturally.
            tech = tech.split(" (")[0]
            for pos, (title, desc, dur) in enumerate(_LESSON_PLAN):
                course.lessons.append(
                    Lesson(
                        title=title.format(tech=tech),
                        description=desc.format(tech=tech),
                        duration=dur,
                        position=pos,
                    )
                )
            added = True
        if added:
            await session.commit()


async def _tech_by_path(session) -> dict:
    """Map (category_slug, subcategory_slug, technology_slug) -> Technology.

    Technologies are loaded with their courses so seeders can check for existing
    courses and compute positions without extra lazy loads.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from .models import Subcategory, Technology

    techs = (
        await session.scalars(
            select(Technology).options(
                selectinload(Technology.courses),
                selectinload(Technology.subcategory).selectinload(Subcategory.category),
            )
        )
    ).all()
    out: dict[tuple[str, str, str], Technology] = {}
    for t in techs:
        sub = t.subcategory
        cat = sub.category if sub else None
        if sub and cat:
            out[(cat.slug, sub.slug, t.slug)] = t
    return out


async def seed_youtube_courses() -> None:
    """Add curated YouTube video-courses (with per-lesson videos), if missing.

    Idempotent: a course is skipped when one with the same title already exists
    under its technology. Each lesson stores the shared video id + a start offset
    so the lessons act as chapters of one long course video.
    """
    from .models import Course, Lesson
    from .seed import SEED_YT_COURSES

    async with SessionLocal() as session:
        by_path = await _tech_by_path(session)
        added = False
        for entry in SEED_YT_COURSES:
            tech = by_path.get(
                (entry["category"], entry["subcategory"], entry["technology"])
            )
            if tech is None:
                continue
            if any(c.title == entry["course"]["title"] for c in tech.courses):
                continue  # already seeded
            c = entry["course"]
            video_id = entry["youtube_id"]
            course = Course(
                technology_id=tech.id,
                title=c["title"], author=c.get("author", ""),
                duration=c.get("duration", ""), url=c.get("url", ""),
                description=c.get("description", ""),
                position=len(tech.courses),
            )
            for pos, lesson in enumerate(entry["lessons"]):
                course.lessons.append(
                    Lesson(
                        title=lesson["title"],
                        description=lesson.get("description", ""),
                        duration=lesson.get("duration", ""),
                        position=pos,
                        youtube_id=lesson.get("youtube_id", video_id),
                        video_start=int(lesson.get("start", 0)),
                    )
                )
            session.add(course)
            added = True
        if added:
            await session.commit()


async def reconcile_video_courses() -> None:
    """Свести засеянные видео-курсы к одному уроку = полное видео.

    Раньше эти курсы дробились на «главы» с выдуманными таймкодами, но на деле
    это одно длинное видео — список показывал много уроков, а играло одно и то же
    видео с начала. Приводим уже существующие курсы к актуальному сиду: оставляем
    ровно один урок (полное видео, темы — в описании), лишние удаляем. Ограничено
    курсами из SEED_YT_COURSES (по названию), чтобы не трогать курсы, добавленные
    ссылкой (там уроки — это разные видео). Идемпотентно: после сведения — no-op.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from .models import Course
    from .seed import SEED_YT_COURSES

    # title -> (youtube_id, единственный урок-спека из сида)
    want = {
        e["course"]["title"]: (e["youtube_id"], e["lessons"][0]) for e in SEED_YT_COURSES
    }
    if not want:
        return
    async with SessionLocal() as session:
        courses = (
            await session.scalars(
                select(Course)
                .where(Course.title.in_(want.keys()))
                .options(selectinload(Course.lessons))
            )
        ).all()
        changed = False
        for course in courses:
            vid, spec = want[course.title]
            lessons = sorted(course.lessons, key=lambda l: (l.position, l.id))
            if not lessons:
                continue  # seed_youtube_courses уже создаст урок на пустом курсе
            keep, *extras = lessons
            for extra in extras:  # лишние «главы» — удаляем
                await session.delete(extra)
                changed = True
            new_title = spec["title"]
            new_desc = spec.get("description", "")
            if (
                keep.title != new_title or keep.description != new_desc
                or keep.video_start != 0 or keep.duration
                or keep.youtube_id != vid or keep.position != 0
            ):
                keep.title = new_title
                keep.description = new_desc
                keep.video_start = 0
                keep.duration = ""
                keep.youtube_id = vid
                keep.position = 0
                changed = True
        if changed:
            await session.commit()


async def seed_link_courses() -> None:
    """Add courses defined by plain YouTube links (see seed.SEED_LINK_COURSES).

    Each lesson's URL is parsed into a video id + start offset, so courses can be
    added by simply pasting links. Idempotent (skips a course whose title already
    exists under its technology); lessons with an unparseable link are skipped,
    and a course with no valid video is not created.
    """
    from .models import Course, Lesson
    from .seed import SEED_LINK_COURSES
    from .youtube import parse_youtube

    async with SessionLocal() as session:
        by_path = await _tech_by_path(session)
        added = False
        for entry in SEED_LINK_COURSES:
            tech = by_path.get(
                (entry["category"], entry["subcategory"], entry["technology"])
            )
            if tech is None:
                continue
            if any(c.title == entry["title"] for c in tech.courses):
                continue  # already seeded
            course = Course(
                technology_id=tech.id,
                title=entry["title"], author=entry.get("author", ""),
                duration=entry.get("duration", ""),
                description=entry.get("description", ""),
                position=len(tech.courses),
            )
            for lesson in entry.get("lessons", []):
                vid, start = parse_youtube(lesson.get("url", ""))
                if not vid:
                    continue  # skip a lesson we couldn't parse a video id from
                course.lessons.append(
                    Lesson(
                        title=lesson["title"],
                        description=lesson.get("description", ""),
                        duration=lesson.get("duration", ""),
                        position=len(course.lessons),
                        youtube_id=vid, video_start=start,
                    )
                )
            if not course.lessons:
                continue  # no playable video → don't add an empty course
            course.url = entry.get("url") or f"https://youtu.be/{course.lessons[0].youtube_id}"
            session.add(course)
            added = True
        if added:
            await session.commit()


async def prune_courses_without_video() -> None:
    """Delete courses that have no lesson with a YouTube video (user preference:
    keep the catalog to real, playable video-courses only).

    Cascades remove each course's lessons/reviews. Any user goal pointing at a
    removed course is cleared so the sidebar falls back to "choose a course".
    Runs on every startup and is stable: deleted placeholder courses are not
    re-seeded (seed_tree only adds courses for brand-new technologies).
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from .models import Course, User

    async with SessionLocal() as session:
        courses = (
            await session.scalars(select(Course).options(selectinload(Course.lessons)))
        ).all()
        to_delete = [c for c in courses if not any(l.youtube_id for l in c.lessons)]
        if not to_delete:
            return
        ids = {c.id for c in to_delete}
        # Clear stale goals that referenced a course we're about to remove.
        users = (
            await session.scalars(select(User).where(User.goal_course_id.in_(ids)))
        ).all()
        for u in users:
            u.goal_course_id = None
        for c in to_delete:
            await session.delete(c)
        await session.commit()
        logging.getLogger("duckie").info(
            "Удалено курсов без видео: %d (оставлены только видео-курсы)", len(to_delete)
        )


async def seed_questions() -> None:
    """Seed quiz questions/options. Incremental: adds any seed question whose text
    is not yet present for its technology, so growing the bank later just works."""
    from sqlalchemy import select

    from .models import Question, QuestionOption
    from .seed import SEED_QUESTIONS

    async with SessionLocal() as session:
        by_path = await _tech_by_path(session)
        added = False
        for entry in SEED_QUESTIONS:
            tech = by_path.get(
                (entry["category"], entry["subcategory"], entry["technology"])
            )
            if tech is None:
                continue
            existing = (
                await session.scalars(
                    select(Question).where(Question.technology_id == tech.id)
                )
            ).all()
            existing_texts = {q.text for q in existing}
            pos = len(existing)
            for q in entry["questions"]:
                if q["text"] in existing_texts:
                    continue  # already seeded this question
                question = Question(technology_id=tech.id, text=q["text"], position=pos)
                pos += 1
                for opos, o in enumerate(q["options"]):
                    question.options.append(
                        QuestionOption(
                            text=o["text"],
                            is_correct=o.get("correct", False),
                            explanation=o.get("explanation", ""),
                            position=opos,
                        )
                    )
                session.add(question)
                added = True
        if added:
            await session.commit()


async def seed_challenges() -> None:
    """Seed code challenges for technologies that have none yet."""
    from sqlalchemy import func, select

    from .models import Challenge
    from .seed import SEED_CHALLENGES

    async with SessionLocal() as session:
        by_path = await _tech_by_path(session)
        added = False
        for entry in SEED_CHALLENGES:
            tech = by_path.get(
                (entry["category"], entry["subcategory"], entry["technology"])
            )
            if tech is None:
                continue
            has = await session.scalar(
                select(func.count()).select_from(Challenge).where(
                    Challenge.technology_id == tech.id
                )
            )
            if has:
                continue  # already seeded for this technology
            for pos, ch in enumerate(entry["challenges"]):
                session.add(
                    Challenge(
                        technology_id=tech.id,
                        title=ch["title"],
                        difficulty=ch.get("difficulty", "easy"),
                        prompt=ch["prompt"],
                        sample_input=ch.get("sample_input", ""),
                        starter_code=ch.get("starter_code", ""),
                        hint=ch.get("hint", ""),
                        answer=ch["answer"],
                        answer_kind=ch.get("answer_kind", "number"),
                        explanation=ch.get("explanation", ""),
                        position=pos,
                    )
                )
                added = True
        if added:
            await session.commit()
