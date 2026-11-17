from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class ProductPricing(Base):
    __tablename__ = "product_pricing"

    __table_args__ = (
        CheckConstraint("base_price > 0", name="ck_pricing_base_price_positive"),
        CheckConstraint("sale_price IS NULL OR sale_price >= 0", name="ck_pricing_sale_price_nonnegative"),
        CheckConstraint("sale_price IS NULL OR sale_price < base_price", name="ck_pricing_sale_price_below_base"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )


class ProductPriceHistory(Base):
    __tablename__ = "product_price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    pricing_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_pricing.id", ondelete="SET NULL"),
        nullable=True
    )
    previous_base_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    new_base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    previous_sale_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    new_sale_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    change_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    changed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
