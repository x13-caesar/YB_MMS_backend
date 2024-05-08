# coding=utf-8

from typing import List, Union

from fastapi import APIRouter, Depends, Header
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_db
from app.services import specification_service, component_service, operation_service

from loguru import logger

router = APIRouter(
    prefix="/components",
    tags=["component"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Component])
def read_unhidden_components(
    db: Session = Depends(get_db),
):
    components = db.query(models.Component).filter(models.Component.hide == False).all()
    return components


@router.get("/hidden", response_model=List[schemas.Component])
def read_hidden_components(db: Session = Depends(get_db)):
    components = component_service.get_hidden_components(db=db)
    return components


@router.get("/all_categories", response_model=List[schemas.CompoCategory])
def read_component_categories(db: Session = Depends(get_db)):
    return component_service.get_compo_categories(db=db)


@router.get("/existing_ids", response_model=List[str])
def read_all_component_ids(db: Session = Depends(get_db)):
    ids = [compo.id for compo in component_service.get_all_ids(db=db)]
    return ids


@router.get("/{component_id}", response_model=schemas.Component)
def read_component_by_id(component_id: str, db: Session = Depends(get_db)):
    component = component_service.get_component(component_id=component_id, db=db)
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return component


@router.get("/name/{name}")
def read_component_by_name(name: str, db: Session = Depends(get_db)):
    component = component_service.get_component_by_name(name=name, db=db)
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return component


@router.get("/name_by_id/{component_id}", response_model=str)
def read_component_name_by_id(component_id: str, db: Session = Depends(get_db)):
    return (
        db.query(models.Component.name)
        .filter(models.Component.id == component_id)
        .first()
    )


@router.get("/category/{category}")
def read_component_by_category(category: str, db: Session = Depends(get_db)):
    component = component_service.get_component_by_category(category=category, db=db)
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return component


@router.get("/low_stock/{component_id}")
def if_component_stock_low(component_id: str, db: Session = Depends(get_db)):
    comp = component_service.get_component(component_id=component_id, db=db)
    specs = specification_service.get_specifications_by_component_id(
        component_id=component_id, db=db
    )
    total_stock = sum([s.stock for s in specs])
    return True if comp.warn_stock > total_stock else False


@router.get("/low_stock", response_model=List[schemas.Component])
def read_components_with_low_stock(db: Session = Depends(get_db)):
    all_components = component_service.get_components(db=db)
    return [
        comp for comp in all_components if if_component_stock_low(component_id=comp.id)
    ]


@router.post("/", response_model=schemas.Component)
def create_component(
    component: schemas.ComponentCreate,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    component.hide = False
    new_compo = component_service.create_component(component=component, db=db)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"创建配件 {new_compo.id} {new_compo.name}", db
    )
    return new_compo


@router.put("/hide/{component_id}")
def hide_component(
    component_id,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db.query(models.Component).filter(models.Component.id == component_id).update(
        {"hide": True}
    )
    db.commit()
    hidden_compo = (
        db.query(models.Component).filter(models.Component.id == component_id).first()
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"隐藏配件 {hidden_compo.id} {hidden_compo.name}", db
    )
    return hidden_compo


@router.put("/unhide/{component_id}")
def unhide_component(
    component_id,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db.query(models.Component).filter(models.Component.id == component_id).update(
        {"hide": False}
    )
    db.commit()
    unhidden_compo = (
        db.query(models.Component).filter(models.Component.id == component_id).first()
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"重显示配件 {unhidden_compo.id} {unhidden_compo.name}", db
    )
    return unhidden_compo


@router.put("/")
def update_component(
    component: schemas.Component,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db_component_data = component_service.get_component(component.id, db=db)
    if not db_component_data:
        raise HTTPException(status_code=400, detail="Matching component not found")
    db_component_model = schemas.Component(**jsonable_encoder(db_component_data))
    update_data = component.dict(exclude_unset=True)
    updated_component = component_service.update_component(
        component=db_component_model.copy(update=update_data), db=db
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"更新配件 {updated_component.id} {updated_component.name}", db
    )
    return updated_component


@router.delete("/{component_id}")
def delete_component(
    component_id: str,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db_component_data = component_service.get_component(component_id, db=db)
    if not db_component_data:
        raise HTTPException(status_code=400, detail="Matching component not found")
    component_service.delete_component(component=db_component_data, db=db)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"删除配件 {db_component_data.id} {db_component_data.name}", db
    )
    return JSONResponse(content={"success": True})
