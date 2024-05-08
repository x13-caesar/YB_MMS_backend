from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder

from app import schemas, models

from app.services import specification_service


def get_component(component_id: str, db: Session):
    return (
        db.query(models.Component).filter(models.Component.id == component_id).first()
    )


def get_components(db: Session):
    return db.query(models.Component).filter(models.Component.hide == False).all()


def get_hidden_components(db: Session):
    return db.query(models.Component).filter(models.Component.hide == True).all()


def get_component_by_category(category: str, db: Session):
    return (
        db.query(models.Component).filter(models.Component.category == category).first()
    )


def get_component_by_name(name: str, db: Session):
    return db.query(models.Component).filter(models.Component.name == name).all()


def if_component_low_stock(component_id: str, db: Session):
    comp = get_component(component_id=component_id, db=db)
    specs = specification_service.get_specifications_by_component_id(
        component_id=component_id, db=db
    )
    total_stock = sum([s.stock for s in specs])
    return True if comp.warn_stock > total_stock else False


def create_component(component: schemas.ComponentCreate, db: Session):
    new_component = models.Component(**component.dict())
    db.add(new_component)
    db.commit()
    db.refresh(new_component)
    return new_component


def update_component(component: schemas.Component, db: Session):
    json_compo = jsonable_encoder(component)
    json_compo.pop("specification")
    updated_component = models.Component(**json_compo)
    db.query(models.Component).filter(
        models.Component.id == updated_component.id
    ).update(jsonable_encoder(updated_component))
    db.commit()
    return (
        db.query(models.Component)
        .filter(models.Component.id == updated_component.id)
        .first()
    )


def delete_component(component: schemas.Component, db: Session):
    db.query(models.Component).filter(models.Component.id == component.id).delete(
        synchronize_session="fetch"
    )
    db.commit()
    return


def get_all_ids(db):
    return db.query(models.Component.id).all()


def get_compo_categories(db):
    return db.query(models.CompoCategory).all()
