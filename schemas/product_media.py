from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductMediaResponse(BaseModel):
    id: int
    product_id: int
    media_type: str
    original_filename: str
    file_size: int
    content_type: str
    is_primary: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
