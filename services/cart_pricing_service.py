from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models.cart import ShoppingCart
from models.product import Product
from models.product_variant import ProductVariant
from models.inventory import Inventory
from schemas.cart_pricing import CartPriceCalculationResponse
from services.product_pricing_service import get_current_product_price
from services.coupon_service import validate_coupon
from utils.checkout_config import (
    SHIPPING_FEE,
    FREE_SHIPPING_THRESHOLD,
    TAX_PERCENTAGE
)


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_cart_price(
    db: Session,
    customer_id: int,
    coupon_code: str | None = None
):
    cart = db.scalar(
        select(ShoppingCart)
        .options(selectinload(ShoppingCart.items))
        .where(
            ShoppingCart.customer_id == customer_id,
            ShoppingCart.status == "ACTIVE"
        )
    )

    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shopping cart is empty"
        )

    subtotal = Decimal("0.00")
    total_items = 0

    for item in cart.items:
        product = db.scalar(
            select(Product).where(
                Product.id == item.product_id,
                Product.is_active.is_(True)
            )
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {item.product_id} is unavailable"
            )

        effective_price = get_current_product_price(
            db, product.id
        )["effective_price"]

        if item.variant_id is not None:
            variant = db.scalar(
                select(ProductVariant).where(
                    ProductVariant.id == item.variant_id,
                    ProductVariant.product_id == product.id,
                    ProductVariant.is_active.is_(True)
                )
            )

            if not variant:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Variant for product {product.id} is unavailable"
                )

            effective_price = (
                Decimal(str(effective_price))
                + Decimal(str(variant.price_adjustment))
            )

        inventory = db.scalar(
            select(Inventory).where(
                Inventory.product_id == item.product_id,
                Inventory.variant_id == item.variant_id
            )
        )

        available_quantity = (
            inventory.available_quantity if inventory else 0
        )

        if item.quantity > available_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.name}"
            )

        if effective_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product price"
            )

        item.unit_price = money(Decimal(str(effective_price)))
        subtotal += item.unit_price * item.quantity
        total_items += item.quantity

    subtotal = money(subtotal)

    discount_amount = Decimal("0.00")
    applied_coupon_code = None

    if coupon_code:
        coupon, discount = validate_coupon(
            db,
            coupon_code,
            subtotal
        )
        discount_amount = money(Decimal(str(discount)))
        applied_coupon_code = coupon.code

    shipping_amount = (
        Decimal("0.00")
        if subtotal >= FREE_SHIPPING_THRESHOLD
        else SHIPPING_FEE
    )

    taxable_amount = money(subtotal - discount_amount)

    tax_amount = money(
        taxable_amount * TAX_PERCENTAGE / Decimal("100")
    )

    total_amount = money(
        taxable_amount + shipping_amount + tax_amount
    )

    db.commit()

    return CartPriceCalculationResponse(
        cart_id=cart.id,
        subtotal=subtotal,
        discount_amount=discount_amount,
        shipping_amount=shipping_amount,
        taxable_amount=taxable_amount,
        tax_percentage=TAX_PERCENTAGE,
        tax_amount=tax_amount,
        total_amount=total_amount,
        total_items=total_items,
        coupon_code=applied_coupon_code
    )
