from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from database.base import Base
from database.connection import engine

import models

from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.customers import router as customers_router
from routers.customer_profiles import router as customer_profiles_router
from routers.addresses import router as addresses_router
from routers.categories import router as categories_router
from routers.brands import router as brands_router
from routers.products import router as products_router
from routers.product_variants import router as product_variants_router
from routers.product_media import router as product_media_router
from routers.product_attributes import router as product_attributes_router
from routers.product_pricing import router as product_pricing_router
from routers.inventory import router as inventory_router
from routers.warehouses import router as warehouses_router
from routers.inventory_transfers import router as inventory_transfers_router
from routers.low_stock import router as low_stock_router
from routers.cart import router as cart_router
from routers.cart_pricing import router as cart_pricing_router
from routers.wishlist import router as wishlist_router
from routers.coupons import router as coupons_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(
    title="ShopSphere Pro API",
    description="Enterprise E-Commerce Management System",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(customers_router)
app.include_router(customer_profiles_router)
app.include_router(addresses_router)
app.include_router(categories_router)
app.include_router(brands_router)
app.include_router(products_router)
app.include_router(product_variants_router)
app.include_router(product_media_router)
app.include_router(product_attributes_router)
app.include_router(product_pricing_router)
app.include_router(inventory_router)
app.include_router(warehouses_router)
app.include_router(inventory_transfers_router)
app.include_router(low_stock_router)
app.include_router(cart_router)
app.include_router(cart_pricing_router)
app.include_router(wishlist_router)
app.include_router(coupons_router)


@app.get("/", tags=["General"])
def root():
    return {"message": "ShopSphere Pro API is running"}


@app.get("/health", tags=["General"])
def health_check():
    return {"status": "healthy"}
