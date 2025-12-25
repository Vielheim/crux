from datetime import datetime
import enum
from typing import Optional, Any
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .database import Base


# Inheriting from str makes it JSON serializable automatically
class ClimbStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)

    # func.now() lets Postgres handle the timestamp (better for consistency)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship: One User has many Climbs
    # cascade="all, delete-orphan" cleans up climbs if the user is deleted
    climbs: Mapped[list["Climb"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Climb(Base):
    __tablename__ = "climbs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # We use native_enum=False usually to store as VARCHAR in DB for easier migrations
    # or strict validation with native_enum=True (Postgres ENUM type)
    status: Mapped[ClimbStatus] = mapped_column(
        enum.Enum(ClimbStatus, name="climb_status_enum", create_type=False),
        default=ClimbStatus.PENDING,
        index=True,
    )

    # S3 Reference
    video_url: Mapped[str] = mapped_column(String)

    # The Analysis Output (YOLO + MediaPipe Data)
    # Stored as JSON so we can evolve the metrics without changing the schema
    analysis_results: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship: A Climb belongs to one User
    user: Mapped["User"] = relationship(back_populates="climbs")
