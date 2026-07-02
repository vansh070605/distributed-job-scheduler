import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class WorkerQueueAssignment(Base):
    worker_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("workers.id", ondelete="CASCADE"), primary_key=True
    )
    queue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("queues.id", ondelete="CASCADE"), primary_key=True
    )

    worker = relationship("Worker", back_populates="queue_assignments")
    queue = relationship("Queue")
