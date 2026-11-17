from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class InventoryTransferHistory(Base):
    __tablename__ = "inventory_transfer_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    transfer_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_transfers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    previous_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    new_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    performed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
