# coding=utf-8

from fastapi import APIRouter, Depends, Header
from typing import List, Union
from app import schemas
from app.services import buyer_service, operation_service
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.dependencies import get_db


router = APIRouter(
    prefix="/buyers",
    tags=["buyer"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Buyer])
def read_buyers(db: Session = Depends(get_db)):
    buyers = buyer_service.get_buyers(db=db)
    return buyers


@router.get("/{buyer_id}", response_model=schemas.Buyer)
def read_buyer(buyer_id: int, db: Session = Depends(get_db)):
    buyer = buyer_service.get_buyer(buyer_id=buyer_id, db=db)
    if buyer is None:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer


@router.get("/name/{name}")
def read_buyer_by_name(name: str, db: Session = Depends(get_db)):
    buyer = buyer_service.get_buyer_by_name(name=name, db=db)
    if buyer is None:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer


@router.get("/company/{company}")
def read_buyer_by_company(company: str, db: Session = Depends(get_db)):
    buyer = buyer_service.get_buyer_by_company(company=company, db=db)
    if buyer is None:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer


@router.post("/", response_model=schemas.Buyer)
def create_buyer(
    buyer: schemas.BuyerCreate,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db_buyer = buyer_service.get_buyer_by_company(company=buyer.company, db=db)
    if db_buyer:
        raise HTTPException(status_code=400, detail="Buyer company already registered")
    new_buyer = buyer_service.create_buyer(buyer=buyer, db=db)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"创建新客户 {new_buyer.name} - {new_buyer.company}", db
    )
    return new_buyer


@router.put("/")
def update_buyer(
    buyer: schemas.Buyer,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db_buyer_data = buyer_service.get_buyer(buyer.id, db=db)
    if not db_buyer_data:
        raise HTTPException(status_code=400, detail="Matching buyer not found")
    db_buyer_model = schemas.Buyer(**jsonable_encoder(db_buyer_data))
    update_data = buyer.dict(exclude_unset=True)
    updated_buyer = buyer_service.update_buyer(
        buyer=db_buyer_model.copy(update=update_data), db=db
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"更新客户信息 {updated_buyer.name} - {updated_buyer.company}", db
    )
    return updated_buyer


@router.delete("/{buyer_id}")
def delete_buyer(buyer_id: int, db: Session = Depends(get_db)):
    db_buyer_data = buyer_service.get_buyer(buyer_id, db=db)
    if not db_buyer_data:
        raise HTTPException(status_code=400, detail="Matching buyer not found")
    buyer_service.delete_buyer(buyer=db_buyer_data, db=db)
    return JSONResponse(content={"success": True})
