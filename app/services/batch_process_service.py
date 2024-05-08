from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app import schemas
from app.models import BatchProcess


def get_batch_process(batch_process_id: int, db: Session):
    return db.query(BatchProcess).filter(BatchProcess.id == batch_process_id).first()


def get_batch_processes(db: Session):
    return db.query(BatchProcess).all()


def get_batch_processes_by_process_id(process_id: int, db: Session):
    return db.query(BatchProcess).filter(BatchProcess.process_id == process_id).all()


def get_batch_processes_by_batch_id(batch_id: int, db: Session):
    return db.query(BatchProcess).filter(BatchProcess.batch_id == batch_id).all()


def get_batch_processes_by_status(status: str, db: Session):
    return db.query(BatchProcess).filter(BatchProcess.status == status).all()


def create_batch_process(batch_process: schemas.BatchProcessCreate, db: Session):
    new_batch_process = BatchProcess(**batch_process.dict())
    db.add(new_batch_process)
    db.commit()
    db.refresh(new_batch_process)
    return new_batch_process


def update_batch_process(batch_process: schemas.BatchProcess, db: Session):
    json_bp = jsonable_encoder(batch_process)
    # remove nested data
    json_process = json_bp.pop("process", None)
    json_work = json_bp.pop("work", None)
    json_wr = json_bp.pop("warehouse_record", None)
    updated_batch_process = BatchProcess(**json_bp)
    db.query(BatchProcess).filter(BatchProcess.id == updated_batch_process.id).update(
        jsonable_encoder(updated_batch_process)
    )
    db.commit()
    return (
        db.query(BatchProcess)
        .filter(BatchProcess.id == updated_batch_process.id)
        .first()
    )


def delete_batch_process(batch_process: schemas.BatchProcess, db: Session):
    db.query(BatchProcess).filter(BatchProcess.id == batch_process.id).delete(
        synchronize_session="fetch"
    )
    db.commit()
    return
