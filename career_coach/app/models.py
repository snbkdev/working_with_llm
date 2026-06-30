"""ORM models."""
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    # what the user is learning now (category slug); null until they pick one
    direction: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # directions the user plans to learn next (list of category slugs)
    planned: Mapped[list] = mapped_column(JSON, default=list, server_default="[]", nullable=False)
    # personal info (filled in from the "Информация" section)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    # URL path to the uploaded avatar (e.g. /static/uploads/avatars/3.png)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # gamification (from docs.md): starts at level 0 / 0 XP
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    icon: Mapped[str] = mapped_column(String(16), default="📚", nullable=False)
    color: Mapped[str] = mapped_column(String(9), default="#5d3fd3", nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subcategories: Mapped[list["Subcategory"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="Subcategory.position",
    )


class Subcategory(Base):
    __tablename__ = "subcategories"
    __table_args__ = (UniqueConstraint("category_id", "slug", name="uq_subcat_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category: Mapped["Category"] = relationship(back_populates="subcategories")
    technologies: Mapped[list["Technology"]] = relationship(
        back_populates="subcategory",
        cascade="all, delete-orphan",
        order_by="Technology.position",
    )


class Technology(Base):
    """Concrete tool/framework under a subcategory, e.g. FastAPI under Python."""

    __tablename__ = "technologies"
    __table_args__ = (UniqueConstraint("subcategory_id", "slug", name="uq_tech_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subcategory_id: Mapped[int] = mapped_column(
        ForeignKey("subcategories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subcategory: Mapped["Subcategory"] = relationship(back_populates="technologies")
    courses: Mapped[list["Course"]] = relationship(
        back_populates="technology",
        cascade="all, delete-orphan",
        order_by="Course.position",
    )


class Course(Base):
    """A specific video course for a technology, by a given author."""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    technology_id: Mapped[int] = mapped_column(
        ForeignKey("technologies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    author: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    # human-readable length, e.g. "12 ч"; free-form so seeds stay simple
    duration: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    technology: Mapped["Technology"] = relationship(back_populates="courses")
