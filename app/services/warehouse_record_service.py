from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app import schemas, models
from app.models import WarehouseRecord


def get_warehouse_record(warehouse_record_id: int, db: Session):
    return (
        db.query(WarehouseRecord)
        .filter(WarehouseRecord.id == warehouse_record_id)
        .first()
    )


def get_warehouse_records(db: Session):
    return db.query(WarehouseRecord).all()


def get_warehouse_records_by_component_id(component_id: str, db: Session):
    return (
        db.query(WarehouseRecord)
        .filter(WarehouseRecord.component_id == component_id)
        .all()
    )


def get_warehouse_records_by_batch_process_id(batch_process_id: int, db: Session):
    return (
        db.query(WarehouseRecord)
        .filter(WarehouseRecord.batch_process_id == batch_process_id)
        .all()
    )


def create_warehouse_record(
    warehouse_record: schemas.WarehouseRecordCreate, db: Session
):
    new_warehouse_record = WarehouseRecord(**warehouse_record.dict())
    db.add(new_warehouse_record)
    db.commit()
    db.refresh(new_warehouse_record)
    return new_warehouse_record


def update_warehouse_record(warehouse_record: schemas.WarehouseRecord, db: Session):
    updated_warehouse_record = WarehouseRecord(**warehouse_record.dict())
    db.query(WarehouseRecord).filter(
        WarehouseRecord.id == updated_warehouse_record.id
    ).update(jsonable_encoder(updated_warehouse_record))
    db.commit()
    return (
        db.query(WarehouseRecord)
        .filter(WarehouseRecord.id == updated_warehouse_record.id)
        .first()
    )


def delete_warehouse_record(warehouse_record: schemas.WarehouseRecord, db: Session):
    db.query(WarehouseRecord).filter(WarehouseRecord.id == warehouse_record.id).delete(
        synchronize_session="fetch"
    )
    db.commit()
    return
