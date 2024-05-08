# coding=utf-8
from fastapi import APIRouter, Depends, Body, Header
from typing import List, Union

from app import models, schemas
from app.services import specification_service, operation_service
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.dependencies import get_db

router = APIRouter(
    prefix="/specifications",
    tags=["specifications"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Specification])
def read_specifications(db: Session = Depends(get_db)):
    specifications = specification_service.get_specifications(db=db)
    return specifications


@router.get("/component/{spec_id}", response_model=schemas.Component)
def get_component_by_specification_id(spec_id: str, db: Session = Depends(get_db)):
    compo_id = (
        db.query(models.Specification.component_id)
        .filter(models.Specification.id == spec_id)
        .first()[0]
    )
    compo = db.query(models.Component).filter(models.Component.id == compo_id).first()
    return compo


@router.get("/component-name/{spec_id}", response_model=str)
def get_component_name_by_specification_id(spec_id: str, db: Session = Depends(get_db)):
    compo_id = (
        db.query(models.Specification.component_id)
        .filter(models.Specification.id == spec_id)
        .first()[0]
    )
    compo_name = (
        db.query(models.Component.name)
        .filter(models.Component.id == compo_id)
        .first()[0]
    )
    return compo_name


@router.get("/hidden", response_model=List[schemas.Specification])
def read_hidden_specifications(db: Session = Depends(get_db)):
    specifications = specification_service.get_specifications(db=db)
    return specifications


@router.get("/existing_ids", response_model=List[str])
def read_all_specification_ids(db: Session = Depends(get_db)):
    ids = [spec.id for spec in specification_service.get_all_ids(db=db)]
    return ids


@router.get("/net_price/{specification_id}")
def read_specification_net_price(specification_id: str, db: Session = Depends(get_db)):
    specification = specification_service.get_specification_net_price_by_id(
        specification_id=specification_id, db=db
    )
    return specification.net_price


@router.get("/gross_price/{specification_id}")
def read_specification_gross_price(
    specification_id: str, db: Session = Depends(get_db)
):
    specification = specification_service.get_specification_gross_price_by_id(
        specification_id=specification_id, db=db
    )
    return specification.gross_price


@router.get("/by_id/{specification_id}", response_model=schemas.Specification)
def read_specification(specification_id: str, db: Session = Depends(get_db)):
    specification = (
        db.query(models.Specification)
        .filter(
            models.Specification.id == specification_id,
        )
        .first()
    )
    if specification is None:
        raise HTTPException(status_code=404, detail="Specification not found")
    return specification


@router.get("/notice/{specification_id}")
def read_notice_by_specification_id(
    specification_id: str, db: Session = Depends(get_db)
):
    specification_notice = (
        db.query(models.Specification.notice)
        .filter(models.Specification.id == specification_id)
        .first()[0]
    )
    if specification_notice is None:
        raise HTTPException(status_code=404, detail="Specification not found")
    return specification_notice


@router.get("/component_id/{component_id}")
def read_specification_by_component_id(
    component_id: str, db: Session = Depends(get_db)
):
    specification = specification_service.get_specifications_by_component_id(
        component_id=component_id, db=db
    )
    if specification is None:
        raise HTTPException(status_code=404, detail="Specification not found")
    return specification


@router.get("/vendor_id/{vendor_id}", response_model=List[schemas.Specification])
def read_specification_by_vendor_id(vendor_id: int, db: Session = Depends(get_db)):
    specification = specification_service.get_specifications_by_vendor_id(
        vendor_id=vendor_id, db=db
    )
    print(vendor_id)
    if specification is None:
        raise HTTPException(status_code=404, detail="Specification not found")

    response = []
    for s in [jsonable_encoder(s) for s in specification]:
        name = (
            db.query(models.Component.name)
            .filter(models.Component.id == s["component_id"])
            .first()
        )
        r = schemas.Specification(component_name=name[0], **s)
        response.append(r)
    return response


@router.get("/price_over/{price}/{gross}")
def read_specification_over_price(
    price: int, gross: bool, db: Session = Depends(get_db)
):
    return specification_service.get_specifications_over_price(
        price=price, gross=gross, db=db
    )


@router.get("/price_equal/{price}/{gross}")
def read_specification_equal_price(
    price: int, gross: bool, db: Session = Depends(get_db)
):
    return specification_service.get_specifications_equal_price(
        price=price, gross=gross, db=db
    )


@router.get("/price_under/{price}/{gross}")
def read_specification_under_price(
    price: int, gross: bool, db: Session = Depends(get_db)
):
    return specification_service.get_specifications_under_price(
        price=price, gross=gross, db=db
    )


@router.get("/if_use_net")
def check_if_spec_use_net_price(spec_id: str, db: Session = Depends(get_db)):
    result = db.query(models.Specification.use_net).filter(models.Specification.id == spec_id).first()[0]
    print(result)
    return {"use_net": result}


@router.post("/", response_model=schemas.Specification)
def create_specification(
    specification: schemas.SpecificationCreate,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    if specification_service.get_specification(
        specification_id=specification.id, db=db
    ):
        raise HTTPException(status_code=400, detail="Existing ID")
    elif specification_service.get_specifications_by_component_id_and_vendor_id(
        component_id=specification.component_id,
        vendor_id=specification.vendor_id,
        db=db,
    ):
        raise HTTPException(
            status_code=400, detail="The vendor already has this component"
        )
    specification.hide = False
    new_spec = specification_service.create_specification(
        specification=specification, db=db
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"创建新配件子类（规格） {new_spec.id}", db
    )
    return new_spec


@router.put("/adjust_stock/{spec_id}/{adjust_number}")
def adjust_stock(
    spec_id: str,
    adjust_number: int,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db_spec = specification_service.get_specification(specification_id=spec_id, db=db)
    db_spec.stock += adjust_number
    updated_spec = specification_service.update_specification(
        specification=db_spec, db=db
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"修改配件子类库存 {updated_spec.id}", db
    )
    return updated_spec


@router.put("/", response_model=schemas.Specification)
def update_specification(
    specification: schemas.SpecificationCreate,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db_specification_data = specification_service.get_specification(
        specification.id, db=db
    )
    if not db_specification_data:
        raise HTTPException(status_code=400, detail="Matching specification not found")
    db_specification_model = schemas.Specification(
        **jsonable_encoder(db_specification_data)
    )
    update_data = specification.dict(exclude_unset=True)
    updated_specification = specification_service.update_specification(
        specification=db_specification_model.copy(update=update_data), db=db
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"修改配件子类（规格）信息 {updated_specification.id}", db
    )
    return updated_specification


@router.put("/hide/{spec_id}", response_model=schemas.Specification)
def hide_specification(
    spec_id: str,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db.query(models.Specification).filter(models.Specification.id == spec_id).update(
        {"hide": True}
    )
    db.commit()
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"停用产品 {spec_id}", db
    )
    return JSONResponse(content={"success": True, "specification_id": spec_id})


@router.put("/unhide/{spec_id}", response_model=schemas.Specification)
def unhide_specification(
    spec_id: str,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db.query(models.Specification).filter(models.Specification.id == spec_id).update(
        {"hide": False}
    )
    db.commit()
    revealed_spec = (
        db.query(models.Specification)
        .filter(models.Specification.id == spec_id)
        .first()
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"停用产品 {revealed_spec.id}", db
    )
    return JSONResponse(content={"success": True})


@router.delete("/{specification_id}")
def delete_specification(specification_id: str, db: Session = Depends(get_db)):
    db_specification_data = specification_service.get_specification(
        specification_id, db=db
    )
    if not db_specification_data:
        raise HTTPException(status_code=400, detail="Matching specification not found")
    specification_service.delete_specification(
        specification=db_specification_data, db=db
    )
    return JSONResponse(content={"success": True})
