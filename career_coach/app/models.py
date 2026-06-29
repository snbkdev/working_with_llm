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
