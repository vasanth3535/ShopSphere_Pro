from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class LowStockThresholdHistory(Base):
    __tablename__ = "low_stock_threshold_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    threshold_id: Mapped[int] = mapped_column(
        ForeignKey("low_stock_thresholds.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    previous_quantity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    new_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    changed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
