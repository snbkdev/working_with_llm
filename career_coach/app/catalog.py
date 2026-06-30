"""Public catalog API: categories and their subcategories (read-only)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .config import TAGLINE
from .db import get_session
from .models import Category, Course, Subcategory, Technology

router = APIRouter(prefix="/api", tags=["catalog"])


def course_dict(c) -> dict:
    return {
        "id": c.id, "title": c.title, "author": c.author,
        "duration": c.duration, "url": c.url,
        "description": c.description, "position": c.position,
        "rating": c.rating, "reviews_count": c.reviews_count,
    }


def tech_dict(t) -> dict:
    return {
        "id": t.id, "slug": t.slug, "title": t.title,
        "description": t.description, "position": t.position,
        "courses": [course_dict(c) for c in t.courses],
    }


def sub_dict(s) -> dict:
    return {
        "id": s.id, "slug": s.slug, "title": s.title,
        "description": s.description, "position": s.position,
        "technologies": [tech_dict(t) for t in s.technologies],
    }


# Eager-load the full category → subcategory → technology → course tree so the
# dict builders never trigger a lazy load under async (which would error).
_TREE_LOADER = (
    selectinload(Category.subcategories)
    .selectinload(Subcategory.technologies)
    .selectinload(Technology.courses)
)


def cat_dict(c) -> dict:
    return {
        "id": c.id, "slug": c.slug, "title": c.title, "icon": c.icon,
        "color": c.color,
        # 'desc' kept for backward compatibility with existing frontend
        "desc": c.description, "description": c.description,
        "position": c.position,
        "subcategories": [sub_dict(s) for s in c.subcategories],
    }


async def _all_categories(db: AsyncSession) -> list[Category]:
    result = await db.scalars(
        select(Category)
        .options(_TREE_LOADER)
        .order_by(Category.position, Category.id)
    )
    return list(result.all())


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_session)) -> dict:
    cats = await _all_categories(db)
    return {"tagline": TAGLINE, "categories": [cat_dict(c) for c in cats]}


@router.get("/categories/{slug}")
async def get_category(slug: str, db: AsyncSession = Depends(get_session)) -> dict:
    cat = await db.scalar(
        select(Category)
        .where(Category.slug == slug)
        .options(_TREE_LOADER)
    )
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Категория не найдена")
    return cat_dict(cat)


async def _load_course_with_tree(course_id: int, db: AsyncSession, *, lessons=False, reviews=False):
    opts = [
        selectinload(Course.technology)
        .selectinload(Technology.subcategory)
        .selectinload(Subcategory.category)
    ]
    if lessons:
        opts.append(selectinload(Course.lessons))
    if reviews:
        opts.append(selectinload(Course.reviews))
    course = await db.scalar(select(Course).where(Course.id == course_id).options(*opts))
    if not course:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Курс не найден")
    return course


def _course_header(course) -> dict:
    """Common course header fields + breadcrumb slugs/titles."""
    tech = course.technology
    sub = tech.subcategory if tech else None
    cat = sub.category if sub else None
    return {
        "id": course.id,
        "title": course.title,
        "author": course.author,
        "duration": course.duration,
        "url": course.url,
        "description": course.description,
        "rating": course.rating,
        "reviews_count": course.reviews_count,
        "technology": tech.title if tech else None,
        "technology_slug": tech.slug if tech else None,
        "subcategory": sub.title if sub else None,
        "subcategory_slug": sub.slug if sub else None,
        "category": (
            {"title": cat.title, "slug": cat.slug, "color": cat.color, "icon": cat.icon}
            if cat
            else None
        ),
    }


@router.get("/courses/{course_id}")
async def course_detail(course_id: int, db: AsyncSession = Depends(get_session)) -> dict:
    """Full course info plus its learning plan (lessons), for the course page."""
    course = await _load_course_with_tree(course_id, db, lessons=True)
    data = _course_header(course)
    data["lessons"] = [
        {
            "id": l.id, "title": l.title, "description": l.description,
            "duration": l.duration, "position": l.position,
        }
        for l in course.lessons
    ]
    return data


@router.get("/courses/{course_id}/reviews")
async def course_reviews(course_id: int, db: AsyncSession = Depends(get_session)) -> dict:
    """Course header info plus its text reviews (for the dedicated reviews page)."""
    course = await _load_course_with_tree(course_id, db, reviews=True)
    data = _course_header(course)
    data["reviews"] = [
        {"id": r.id, "author": r.author, "rating": r.rating, "text": r.text}
        for r in course.reviews
    ]
    return data
