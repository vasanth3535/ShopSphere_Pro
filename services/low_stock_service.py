from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.inventory import Inventory
from models.low_stock import LowStockThreshold, LowStockAlert
from models.low_stock_history import LowStockThresholdHistory
from schemas.low_stock import (
    LowStockThresholdCreate,
    LowStockThresholdUpdate
)


def get_inventory(db: Session, inventory_id: int):
    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found"
        )

    return inventory


def get_threshold(db: Session, threshold_id: int):
    threshold = db.query(LowStockThreshold).filter(
        LowStockThreshold.id == threshold_id
    ).first()

    if not threshold:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Low-stock threshold not found"
        )

    return threshold


def add_threshold_history(
    db: Session,
    threshold_id: int,
    previous_quantity: int | None,
    new_quantity: int,
    user_id: int,
    notes: str | None = None
):
    history = LowStockThresholdHistory(
        threshold_id=threshold_id,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        changed_by=user_id,
        notes=notes
    )

    db.add(history)


def synchronize_alert(db: Session, threshold: LowStockThreshold):
    inventory = get_inventory(db, threshold.inventory_id)

    open_alerts = db.query(LowStockAlert).filter(
        LowStockAlert.threshold_id == threshold.id,
        LowStockAlert.status == "OPEN"
    ).all()

    if not threshold.is_active:
        for alert in open_alerts:
            alert.status = "RESOLVED"
            alert.resolved_at = datetime.now()
        return

    current_quantity = inventory.available_quantity

    if current_quantity <= threshold.minimum_quantity:
        if not open_alerts:
            alert = LowStockAlert(
                inventory_id=inventory.id,
                threshold_id=threshold.id,
                current_quantity=current_quantity,
                minimum_quantity=threshold.minimum_quantity,
                status="OPEN",
                message=(
                    f"Low stock alert: available quantity is "
                    f"{current_quantity}, minimum required quantity is "
                    f"{threshold.minimum_quantity}"
                )
            )
            db.add(alert)
        else:
            for alert in open_alerts:
                alert.current_quantity = current_quantity
                alert.minimum_quantity = threshold.minimum_quantity
                alert.message = (
                    f"Low stock alert: available quantity is "
                    f"{current_quantity}, minimum required quantity is "
                    f"{threshold.minimum_quantity}"
                )
    else:
        for alert in open_alerts:
            alert.status = "RESOLVED"
            alert.resolved_at = datetime.now()


def create_threshold(
    db: Session,
    data: LowStockThresholdCreate,
    user_id: int
):
    get_inventory(db, data.inventory_id)

    existing = db.query(LowStockThreshold).filter(
        LowStockThreshold.inventory_id == data.inventory_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A threshold already exists for this inventory"
        )

    threshold = LowStockThreshold(
        inventory_id=data.inventory_id,
        minimum_quantity=data.minimum_quantity,
        created_by=user_id
    )

    db.add(threshold)
    db.flush()

    add_threshold_history(
        db,
        threshold.id,
        None,
        data.minimum_quantity,
        user_id,
        "Initial low-stock threshold configured"
    )

    synchronize_alert(db, threshold)

    db.commit()
    db.refresh(threshold)
    return threshold


def list_thresholds(
    db: Session,
    active_only: bool = False
):
    query = db.query(LowStockThreshold)

    if active_only:
        query = query.filter(
            LowStockThreshold.is_active.is_(True)
        )

    thresholds = query.order_by(
        LowStockThreshold.id.desc()
    ).all()

    for threshold in thresholds:
        synchronize_alert(db, threshold)

    db.commit()
    return thresholds


def update_threshold(
    db: Session,
    threshold_id: int,
    data: LowStockThresholdUpdate,
    user_id: int
):
    threshold = get_threshold(db, threshold_id)
    updates = data.model_dump(exclude_unset=True)

    new_quantity = updates.get(
        "minimum_quantity",
        threshold.minimum_quantity
    )

    if new_quantity is None:
        new_quantity = threshold.minimum_quantity

    if new_quantity != threshold.minimum_quantity:
        add_threshold_history(
            db,
            threshold.id,
            threshold.minimum_quantity,
            new_quantity,
            user_id,
            updates.get("notes")
        )

    if "minimum_quantity" in updates:
        threshold.minimum_quantity = new_quantity

    if "is_active" in updates and updates["is_active"] is not None:
        threshold.is_active = updates["is_active"]

    synchronize_alert(db, threshold)

    db.commit()
    db.refresh(threshold)
    return threshold


def get_low_stock_alerts(
    db: Session,
    alert_status: str | None = None
):
    query = db.query(LowStockAlert)

    if alert_status:
        query = query.filter(
            LowStockAlert.status == alert_status
        )

    alerts = query.order_by(
        LowStockAlert.created_at.desc(),
        LowStockAlert.id.desc()
    ).all()

    return alerts


def get_low_stock_report(db: Session):
    thresholds = db.query(LowStockThreshold).filter(
        LowStockThreshold.is_active.is_(True)
    ).all()

    report = []

    for threshold in thresholds:
        inventory = get_inventory(db, threshold.inventory_id)

        if inventory.available_quantity <= threshold.minimum_quantity:
            report.append({
                "inventory_id": inventory.id,
                "product_id": inventory.product_id,
                "variant_id": inventory.variant_id,
                "total_quantity": inventory.total_quantity,
                "reserved_quantity": inventory.reserved_quantity,
                "available_quantity": inventory.available_quantity,
                "minimum_quantity": threshold.minimum_quantity,
                "shortage_quantity": max(
                    threshold.minimum_quantity - inventory.available_quantity,
                    0
                )
            })

        synchronize_alert(db, threshold)

    db.commit()
    return report


def get_threshold_history(db: Session, threshold_id: int):
    get_threshold(db, threshold_id)

    return db.query(LowStockThresholdHistory).filter(
        LowStockThresholdHistory.threshold_id == threshold_id
    ).order_by(
        LowStockThresholdHistory.created_at.desc(),
        LowStockThresholdHistory.id.desc()
    ).all()


def resolve_alert(db: Session, alert_id: int):
    alert = db.query(LowStockAlert).filter(
        LowStockAlert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Low-stock alert not found"
        )

    threshold = get_threshold(db, alert.threshold_id)
    synchronize_alert(db, threshold)

    db.commit()
    db.refresh(alert)

    if alert.status == "OPEN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert cannot be resolved while stock remains below threshold"
        )

    return alert
