from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models.cart import ShoppingCart, CartItem
from models.product import Product
from models.product_variant import ProductVariant
from models.inventory import Inventory


def get_or_create_cart(db: Session, customer_id: int):
    cart = db.scalar(
        select(ShoppingCart)
        .where(
            ShoppingCart.customer_id == customer_id,
            ShoppingCart.status == "ACTIVE"
        )
        .with_for_update()
    )

    if cart:
        return cart

    cart = ShoppingCart(customer_id=customer_id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def get_product_and_price(
    db: Session,
    product_id: int,
    variant_id: int | None
):
    product = db.scalar(
        select(Product)
        .where(Product.id == product_id, Product.is_active.is_(True))
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active product not found"
        )

    if variant_id is not None:
        variant = db.scalar(
            select(ProductVariant).where(
                ProductVariant.id == variant_id,
                ProductVariant.product_id == product_id,
                ProductVariant.is_active.is_(True)
            )
        )

        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active product variant not found"
            )

        price = Decimal(str(product.base_price)) + Decimal(
            str(variant.price_adjustment or 0)
        )
    else:
        price = Decimal(str(product.base_price))

    if price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product price cannot be negative"
        )

    return product, price


def get_available_stock(
    db: Session,
    product_id: int,
    variant_id: int | None
):
    inventory = db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.variant_id == variant_id
        )
    )

    return inventory.available_quantity if inventory else 0


def get_cart(db: Session, customer_id: int):
    cart = db.scalar(
        select(ShoppingCart)
        .options(selectinload(ShoppingCart.items))
        .where(
            ShoppingCart.customer_id == customer_id,
            ShoppingCart.status == "ACTIVE"
        )
    )

    if not cart:
        cart = get_or_create_cart(db, customer_id)
        cart = db.scalar(
            select(ShoppingCart)
            .options(selectinload(ShoppingCart.items))
            .where(ShoppingCart.id == cart.id)
        )

    return build_cart_response(cart)


def build_cart_response(cart: ShoppingCart):
    items = list(cart.items)
    subtotal = sum(
        (
            Decimal(str(item.unit_price)) * item.quantity
            for item in items
        ),
        Decimal("0.00")
    )

    return {
        "id": cart.id,
        "customer_id": cart.customer_id,
        "status": cart.status,
        "items": items,
        "subtotal": subtotal,
        "total_items": sum(item.quantity for item in items),
        "created_at": cart.created_at,
        "updated_at": cart.updated_at
    }


def add_cart_item(
    db: Session,
    customer_id: int,
    product_id: int,
    variant_id: int | None,
    quantity: int
):
    cart = get_or_create_cart(db, customer_id)

    product, price = get_product_and_price(
        db, product_id, variant_id
    )

    available = get_available_stock(
        db, product_id, variant_id
    )

    existing = db.scalar(
        select(CartItem)
        .where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id,
            CartItem.variant_id == variant_id
        )
        .with_for_update()
    )

    requested_quantity = quantity + (
        existing.quantity if existing else 0
    )

    if requested_quantity > available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {available} units are currently available"
        )

    if existing:
        existing.quantity = requested_quantity
        existing.unit_price = price
    else:
        db.add(
            CartItem(
                cart_id=cart.id,
                product_id=product.id,
                variant_id=variant_id,
                quantity=quantity,
                unit_price=price
            )
        )

    db.commit()
    return get_cart(db, customer_id)


def update_cart_item(
    db: Session,
    customer_id: int,
    item_id: int,
    quantity: int
):
    cart = get_or_create_cart(db, customer_id)

    item = db.scalar(
        select(CartItem)
        .where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
        .with_for_update()
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )

    available = get_available_stock(
        db, item.product_id, item.variant_id
    )

    if quantity > available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {available} units are currently available"
        )

    _, price = get_product_and_price(
        db, item.product_id, item.variant_id
    )

    item.quantity = quantity
    item.unit_price = price

    db.commit()
    return get_cart(db, customer_id)


def remove_cart_item(
    db: Session,
    customer_id: int,
    item_id: int
):
    cart = get_or_create_cart(db, customer_id)

    item = db.scalar(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )

    db.delete(item)
    db.commit()
    return get_cart(db, customer_id)
