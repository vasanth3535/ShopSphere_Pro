from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class LowStockThreshold(Base):
    __tablename__ = "low_stock_thresholds"

    __table_args__ = (
        UniqueConstraint(
            "inventory_id",
            name="uq_low_stock_inventory"
        ),
        CheckConstraint(
            "minimum_quantity >= 0",
            name="ck_low_stock_minimum_nonnegative"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    minimum_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class LowStockAlert(Base):
    __tablename__ = "low_stock_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    threshold_id: Mapped[int] = mapped_column(
        ForeignKey("low_stock_thresholds.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    current_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    minimum_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="OPEN",
        nullable=False,
        index=True
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
