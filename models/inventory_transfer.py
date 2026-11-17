from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class InventoryTransfer(Base):
    __tablename__ = "inventory_transfers"

    __table_args__ = (
        CheckConstraint(
            "requested_quantity > 0",
            name="ck_transfer_requested_positive"
        ),
        CheckConstraint(
            "dispatched_quantity >= 0",
            name="ck_transfer_dispatched_nonnegative"
        ),
        CheckConstraint(
            "received_quantity >= 0",
            name="ck_transfer_received_nonnegative"
        ),
        CheckConstraint(
            "dispatched_quantity <= requested_quantity",
            name="ck_transfer_dispatched_lte_requested"
        ),
        CheckConstraint(
            "received_quantity <= dispatched_quantity",
            name="ck_transfer_received_lte_dispatched"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    transfer_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    source_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"),
        nullable=False,
        index=True
    )

    destination_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"),
        nullable=False,
        index=True
    )

    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.id"),
        nullable=False,
        index=True
    )

    requested_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    dispatched_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    received_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="REQUESTED",
        nullable=False,
        index=True
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    requested_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    dispatched_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    received_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    dispatched_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
