from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app import schemas, models


def get_work_specification(work_specification_id: int, db: Session):
    return (
        db.query(models.WorkSpecification)
        .filter(models.WorkSpecification.id == work_specification_id)
        .first()
    )


def get_work_specifications(db: Session):
    return db.query(models.WorkSpecification).all()


def get_work_specifications_by_work_id(work_id: int, db: Session):
    return (
        db.query(models.WorkSpecification)
        .filter(models.WorkSpecification.work_id == work_id)
        .all()
    )


def get_work_specifications_by_specification_id(specification_id: int, db: Session):
    return (
        db.query(models.WorkSpecification)
        .filter(models.WorkSpecification.specification_id == specification_id)
        .all()
    )


def get_work_specifications_not_fulfilled(db: Session):
    return (
        db.query(models.WorkSpecification)
        .filter(
            models.WorkSpecification.plan_amount
            > models.WorkSpecification.actual_amount
        )
        .all()
    )


def create_work_specification(
    work_specification: schemas.WorkSpecificationCreate, db: Session
):
    new_work_specification = models.WorkSpecification(**work_specification.dict())
    db.add(new_work_specification)
    db.commit()
    db.refresh(new_work_specification)
    return new_work_specification


def update_work_specification(
    work_specification: schemas.WorkSpecification, db: Session
):
    updated_work_specification = models.WorkSpecification(**work_specification.dict())
    db.query(models.WorkSpecification).filter(
        models.WorkSpecification.id == updated_work_specification.id
    ).update(jsonable_encoder(updated_work_specification))
    db.commit()
    return (
        db.query(models.WorkSpecification)
        .filter(models.WorkSpecification.id == updated_work_specification.id)
        .first()
    )


def delete_work_specification(
    work_specification: schemas.WorkSpecification, db: Session
):
    db.query(models.WorkSpecification).filter(
        models.WorkSpecification.id == work_specification.id
    ).delete(synchronize_session="fetch")
    db.commit()
    return
