from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class WarehouseInventory(Base):
    __tablename__ = "warehouse_inventory"

    __table_args__ = (
        UniqueConstraint(
            "warehouse_id",
            "inventory_id",
            name="uq_warehouse_inventory"
        ),
        CheckConstraint("total_quantity >= 0", name="ck_warehouse_total_nonnegative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_warehouse_reserved_nonnegative"),
        CheckConstraint(
            "reserved_quantity <= total_quantity",
            name="ck_warehouse_reserved_lte_total"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    total_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
