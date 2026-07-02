from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class Worker(Base):
    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # unique worker name
    hostname: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, offline
    concurrency: Mapped[int] = mapped_column(Integer, default=10)
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    queue_assignments = relationship(
        "WorkerQueueAssignment", back_populates="worker", cascade="all, delete-orphan"
    )
