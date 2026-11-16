import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models.product import Product
from models.product_media import ProductMedia


UPLOAD_DIRS = {
    "IMAGE": Path("uploads/product_images"),
    "DOCUMENT": Path("uploads/product_documents")
}

ALLOWED_FILES = {
    "IMAGE": {
        "image/jpeg",
        "image/png",
        "image/webp"
    },
    "DOCUMENT": {
        "application/pdf",
        "text/plain"
    }
}

MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_product(db: Session, product_id: int):
    product = db.get(Product, product_id)

    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active product not found"
        )

    return product


def upload_product_media(
    db: Session,
    product_id: int,
    file: UploadFile,
    media_type: str,
    is_primary: bool = False
):
    validate_product(db, product_id)

    media_type = media_type.upper()

    if media_type not in ALLOWED_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media type must be IMAGE or DOCUMENT"
        )

    if file.content_type not in ALLOWED_FILES[media_type]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format"
        )

    extension = Path(file.filename or "").suffix.lower()

    allowed_extensions = {
        "IMAGE": {".jpg", ".jpeg", ".png", ".webp"},
        "DOCUMENT": {".pdf", ".txt"}
    }

    if extension not in allowed_extensions[media_type]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension does not match the allowed formats"
        )

    file_content = file.file.read()

    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Maximum file size is 10 MB"
        )

    if media_type == "IMAGE" and not file_content.startswith(
        (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"RIFF")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file content"
        )

    if media_type == "DOCUMENT" and extension == ".pdf" and not file_content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file content"
        )

    if media_type == "DOCUMENT" and extension == ".txt" and b"\x00" in file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid text file content"
        )

    upload_directory = UPLOAD_DIRS[media_type]
    upload_directory.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid.uuid4().hex}{extension}"
    file_path = upload_directory / stored_filename

    if is_primary and media_type == "IMAGE":
        db.execute(
            update(ProductMedia)
            .where(
                ProductMedia.product_id == product_id,
                ProductMedia.media_type == "IMAGE"
            )
            .values(is_primary=False)
        )

    try:
        with file_path.open("xb") as destination:
            destination.write(file_content)

        media = ProductMedia(
            product_id=product_id,
            media_type=media_type,
            original_filename=Path(file.filename or "upload").name,
            stored_filename=stored_filename,
            file_path=str(file_path),
            file_size=len(file_content),
            content_type=file.content_type,
            is_primary=is_primary if media_type == "IMAGE" else False
        )

        db.add(media)
        db.commit()
        db.refresh(media)

        return media

    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise


def list_product_media(
    db: Session,
    product_id: int,
    media_type: str | None = None
):
    validate_product(db, product_id)

    query = select(ProductMedia).where(
        ProductMedia.product_id == product_id
    )

    if media_type:
        media_type = media_type.upper()

        if media_type not in ALLOWED_FILES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Media type must be IMAGE or DOCUMENT"
            )

        query = query.where(ProductMedia.media_type == media_type)

    return db.scalars(
        query.order_by(ProductMedia.is_primary.desc(), ProductMedia.created_at.desc())
    ).all()


def delete_product_media(db: Session, media_id: int):
    media = db.get(ProductMedia, media_id)

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product media not found"
        )

    db.delete(media)
    db.commit()

    Path(media.file_path).unlink(missing_ok=True)

    return {"message": "Product media deleted successfully"}
