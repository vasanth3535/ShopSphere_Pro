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


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(
    title="ShopSphere Pro - E-Commerce Backend",
    description="Enterprise E-Commerce Backend API",
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


@app.get("/", tags=["General"])
def root():
    return {"message": "ShopSphere Pro API is running"}


@app.get("/health", tags=["General"])
def health_check():
    return {"status": "healthy"}
