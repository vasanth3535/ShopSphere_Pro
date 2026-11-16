from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.category import Category
from schemas.category import CategoryCreate, CategoryUpdate


def validate_parent_category(db: Session, parent_id: int | None, category_id: int | None = None):
    if parent_id is None:
        return

    if category_id is not None and parent_id == category_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category cannot be its own parent"
        )

    parent = db.get(Category, parent_id)

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent category not found"
        )


def create_category(db: Session, data: CategoryCreate):
    validate_parent_category(db, data.parent_id)

    category = Category(**data.model_dump())
    db.add(category)

    try:
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name or slug already exists"
        )

    return category


def list_categories(db: Session, include_inactive: bool = False):
    query = select(Category).order_by(Category.name)

    if not include_inactive:
        query = query.where(Category.is_active.is_(True))

    return db.scalars(query).all()


def get_category(db: Session, category_id: int):
    category = db.get(Category, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate):
    category = get_category(db, category_id)
    update_data = data.model_dump(exclude_unset=True)

    if "parent_id" in update_data:
        validate_parent_category(db, update_data["parent_id"], category_id)

    for field, value in update_data.items():
        setattr(category, field, value)

    try:
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name or slug already exists"
        )

    return category


def delete_category(db: Session, category_id: int):
    category = get_category(db, category_id)

    child_exists = db.scalar(
        select(Category.id).where(Category.parent_id == category_id).limit(1)
    )

    if child_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a category that has child categories"
        )

    db.delete(category)
    db.commit()

    return {"message": "Category deleted successfully"}
