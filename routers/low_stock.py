from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.low_stock import (
    LowStockThresholdCreate,
    LowStockThresholdUpdate,
    LowStockThresholdResponse,
    LowStockAlertResponse,
    LowStockHistoryResponse,
    LowStockReportItem
)
from services import low_stock_service
from utils.dependencies import get_current_user
from utils.permissions import require_roles


router = APIRouter(
    prefix="/low-stock",
    tags=["MODULE 16 - Low-Stock Management"]
)

low_stock_access = require_roles(
    "SUPER_ADMIN",
    "ADMIN",
    "INVENTORY_MANAGER"
)


@router.post(
    "/thresholds",
    response_model=LowStockThresholdResponse,
    status_code=status.HTTP_201_CREATED
)
def create_threshold(
    data: LowStockThresholdCreate,
    db: Session = Depends(get_db),
    current_user=Depends(low_stock_access)
):
    return low_stock_service.create_threshold(
        db, data, current_user.id
    )


@router.get(
    "/thresholds",
    response_model=list[LowStockThresholdResponse]
)
def list_thresholds(
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user=Depends(low_stock_access)
):
    return low_stock_service.list_thresholds(db, active_only)


@router.patch(
    "/thresholds/{threshold_id}",
    response_model=LowStockThresholdResponse
)
def update_threshold(
    threshold_id: int,
    data: LowStockThresholdUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(low_stock_access)
):
    return low_stock_service.update_threshold(
        db, threshold_id, data, current_user.id
    )


@router.get(
    "/thresholds/{threshold_id}/history",
    response_model=list[LowStockHistoryResponse]
)
def get_threshold_history(
    threshold_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(low_stock_access)
):
    return low_stock_service.get_threshold_history(
        db, threshold_id
    )


@router.get(
    "/alerts",
    response_model=list[LowStockAlertResponse]
)
def get_low_stock_alerts(
    alert_status: Literal["OPEN", "RESOLVED"] | None = Query(
        default=None,
        alias="status"
    ),
    db: Session = Depends(get_db),
    current_user=Depends(low_stock_access)
):
    return low_stock_service.get_low_stock_alerts(
        db, alert_status
    )


@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=LowStockAlertResponse
)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(low_stock_access)
):
    return low_stock_service.resolve_alert(db, alert_id)


@router.get(
    "/report",
    response_model=list[LowStockReportItem]
)
def get_low_stock_report(
    db: Session = Depends(get_db),
    current_user=Depends(low_stock_access)
):
    return low_stock_service.get_low_stock_report(db)
