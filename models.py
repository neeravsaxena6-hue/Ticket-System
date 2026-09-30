from datetime import datetime

from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    manager_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    manager_responded_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    is_escalated: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    escalated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )