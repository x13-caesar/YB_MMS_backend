from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app import schemas, models


def get_specification(specification_id: str, db: Session):
    return (
        db.query(models.Specification)
        .filter(
            models.Specification.id == specification_id,
            models.Specification.hide == False,
        )
        .first()
    )


def get_specifications(db: Session):
    return db.query(models.Specification).all()


def get_hidden_specifications(db: Session):
    return (
        db.query(models.Specification).filter(models.Specification.hide == True).all()
    )


def get_specification_net_price_by_id(specification_id: str, db: Session):
    return (
        db.query(models.Specification.net_price)
        .filter(models.Specification.id == specification_id)
        .first()
    )


def get_specification_gross_price_by_id(specification_id: str, db: Session):
    return (
        db.query(models.Specification.gross_price)
        .filter(models.Specification.id == specification_id)
        .first()
    )


def get_specifications_by_component(component: models.Component, db: Session):
    return (
        db.query(models.Specification)
        .filter(models.Specification.component_id == component.id)
        .all()
    )


def get_specifications_by_component_id(component_id: str, db: Session):
    return (
        db.query(models.Specification)
        .filter(models.Specification.component_id == component_id)
        .all()
    )


def get_specifications_by_vendor_id(vendor_id: int, db: Session):
    return (
        db.query(models.Specification)
        .filter(models.Specification.vendor_id == vendor_id)
        .all()
    )


def get_specifications_by_component_id_and_vendor_id(
    component_id: str, vendor_id: int, db: Session
):
    return (
        db.query(models.Specification)
        .filter(
            models.Specification.vendor_id == vendor_id,
            models.Specification.component_id == component_id,
        )
        .all()
    )


def get_specifications_over_price(price: int, gross: bool, db: Session):
    if gross:
        return (
            db.query(models.Specification)
            .filter(models.Specification.gross_price > price)
            .all()
        )
    else:
        return (
            db.query(models.Specification)
            .filter(models.Specification.net_price > price)
            .all()
        )


def get_specifications_equal_price(price: int, gross: bool, db: Session):
    if gross:
        return (
            db.query(models.Specification)
            .filter(models.Specification.gross_price == price)
            .all()
        )
    else:
        return (
            db.query(models.Specification)
            .filter(models.Specification.net_price == price)
            .all()
        )


def get_specifications_under_price(price: int, gross: bool, db: Session):
    if gross:
        return (
            db.query(models.Specification)
            .filter(models.Specification.gross_price < price)
            .all()
        )
    else:
        return (
            db.query(models.Specification)
            .filter(models.Specification.net_price < price)
            .all()
        )


def create_specification(specification: schemas.SpecificationCreate, db: Session):
    new_specification = models.Specification(**specification.dict())
    db.add(new_specification)
    db.commit()
    db.refresh(new_specification)
    return new_specification


def update_specification(specification: schemas.Specification, db: Session):
    json_spec = jsonable_encoder(specification)
    for attr in ["id", "vendor", "component_name", "vendor_company", "display_vendor_id", "vendor_id", "component_id"]:
        json_spec.pop(attr, None)
    db.query(models.Specification).filter(
        models.Specification.id == specification.id
    ).update(json_spec)
    db.commit()
    return (
        db.query(models.Specification)
        .filter(models.Specification.id == specification.id)
        .first()
    )


def delete_specification(specification: schemas.Specification, db: Session):
    db.query(models.Specification).filter(
        models.Specification.id == specification.id
    ).delete(synchronize_session="fetch")
    db.commit()
    return {"success": True, "detail": ""}


def get_all_ids(db):
    return db.query(models.Specification.id).all()
