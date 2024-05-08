from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app import schemas, models


def get_process_component(process_component_id: int, db: Session):
    return (
        db.query(models.ProcessComponent)
        .filter(models.ProcessComponent.id == process_component_id)
        .first()
    )


def get_process_components(db: Session):
    return db.query(models.ProcessComponent).all()


def get_process_components_by_process_id(process_id: str, db: Session):
    return (
        db.query(models.ProcessComponent)
        .filter(models.ProcessComponent.process_id == process_id)
        .all()
    )


def get_process_components_by_component_id(component_id: str, db: Session):
    return (
        db.query(models.ProcessComponent)
        .filter(models.ProcessComponent.component_id == component_id)
        .all()
    )


def create_process_component(
    process_component: schemas.ProcessComponentCreate, db: Session
):
    json_pc = jsonable_encoder(process_component)
    json_pc.pop("component")
    new_process_component = models.ProcessComponent(**json_pc)
    db.add(new_process_component)
    db.commit()
    db.refresh(new_process_component)
    return new_process_component


def update_process_component(process_component: schemas.ProcessComponent, db: Session):
    updated_process_component = models.ProcessComponent(**process_component.dict())
    db.query(models.ProcessComponent).filter(
        models.ProcessComponent.id == updated_process_component.id
    ).update(jsonable_encoder(updated_process_component))
    db.commit()
    return (
        db.query(models.ProcessComponent)
        .filter(models.ProcessComponent.id == updated_process_component.id)
        .first()
    )


def delete_process_component(process_component: schemas.ProcessComponent, db: Session):
    db.query(models.ProcessComponent).filter(
        models.ProcessComponent.id == process_component.id
    ).delete(synchronize_session="fetch")
    db.commit()
    return
