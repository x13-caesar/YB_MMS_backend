from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app import schemas, models


def get_process(process_id: str, db: Session):
    return db.query(models.Process).filter(models.Process.id == process_id).first()


def get_processes(db: Session):
    return db.query(models.Process).all()


def get_processes_by_name(name: str, db: Session):
    return db.query(models.Process).filter(models.Process.name == name).all()


def get_processes_by_product_id(product_id: str, db: Session):
    return (
        db.query(models.Process).filter(models.Process.product_id == product_id).all()
    )


def create_process(process: schemas.ProcessCreate, db: Session):
    new_process = models.Process(**process.dict())
    db.add(new_process)
    db.commit()
    db.refresh(new_process)
    return new_process


def update_process(process: schemas.Process, db: Session):
    updated_process = models.Process(**process.dict())
    db.query(models.Process).filter(models.Process.id == updated_process.id).update(
        jsonable_encoder(updated_process)
    )
    db.commit()
    return (
        db.query(models.Process).filter(models.Process.id == updated_process.id).first()
    )


def delete_process(process: schemas.Process, db: Session):
    db.query(models.Process).filter(models.Process.id == process.id).delete(
        synchronize_session="fetch"
    )
    db.commit()
    return
