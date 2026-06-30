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

    Runs only when the technologies table is empty, so it works both on a fresh
    DB and on an older one that already has categories/subcategories.
    """
    from sqlalchemy import func, select
    from sqlalchemy.orm import selectinload

    from .models import Category, Course, Subcategory, Technology
    from .seed import SEED_CATEGORIES

    async with SessionLocal() as session:
        existing = await session.scalar(select(func.count()).select_from(Technology))
        if existing:
            return

        # Map (category_slug, subcategory_slug) -> Subcategory for lookups.
        cats = (
            await session.scalars(
                select(Category).options(selectinload(Category.subcategories))
            )
        ).all()
        subs: dict[tuple[str, str], Subcategory] = {
            (cat.slug, sub.slug): sub for cat in cats for sub in cat.subcategories
        }

        for cat in SEED_CATEGORIES:
            for sub in cat["subcategories"]:
                target = subs.get((cat["slug"], sub["slug"]))
                if target is None:
                    continue
                for tpos, tech in enumerate(sub.get("technologies", [])):
                    technology = Technology(
                        subcategory_id=target.id, slug=tech["slug"],
                        title=tech["title"], description=tech["description"], position=tpos,
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
        await session.commit()
