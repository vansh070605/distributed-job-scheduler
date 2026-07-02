import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class Queue(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    concurrency: Mapped[int] = mapped_column(Integer, default=10)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    rate_limit: Mapped[int] = mapped_column(Integer, nullable=True)  # operations per second
    retry_policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("retrypolicies.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    project = relationship("Project", back_populates="queues")
    retry_policy = relationship("RetryPolicy", back_populates="queues")
    jobs = relationship("Job", back_populates="queue", cascade="all, delete-orphan")
    metrics = relationship("QueueMetrics", back_populates="queue", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_queues_project_name"),
    )
