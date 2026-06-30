"""Async SQLAlchemy engine, session factory and Base."""
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
        ):
            await conn.execute(text(ddl))

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
