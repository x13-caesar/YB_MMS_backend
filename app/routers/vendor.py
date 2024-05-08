# coding=utf-8
from fastapi import APIRouter, Depends, Header
from typing import List, Union


from app.services import vendor_service, operation_service
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.dependencies import get_db

from app import schemas, models

router = APIRouter(
    prefix="/vendors",
    tags=["vendor"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Vendor])
def read_vendors(db: Session = Depends(get_db)):
    vendors = vendor_service.get_vendors(db=db)
    for v in vendors:
        v.id = str(v.id).rjust(3, '0')
    return vendors


@router.get("/{vendor_id}", response_model=schemas.Vendor)
def read_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = vendor_service.get_vendor(vendor_id=vendor_id, db=db)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor.id = str(vendor.id).rjust(3, '0')
    return vendor


@router.get("/name/{name}")
def read_vendor_by_name(name: str, db: Session = Depends(get_db)):
    vendor = vendor_service.get_vendor_by_name(name=name, db=db)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.get("/company/{company}")
def read_vendor_by_company(company: str, db: Session = Depends(get_db)):
    vendor = vendor_service.get_vendor_by_company(company=company, db=db)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor.id = str(vendor.id).rjust(3, '0')
    return vendor


@router.post("/")
def create_vendor(
    vendor: schemas.VendorCreate,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db_vendor = vendor_service.get_vendor_by_company(company=vendor.company, db=db)
    if db_vendor:
        raise HTTPException(status_code=400, detail="Vendor company already registered")
    new_vendor = vendor_service.create_vendor(vendor=vendor, db=db)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"创建新供应商 {new_vendor.name} {new_vendor.company}", db
    )
    return new_vendor


@router.put("/{vendor_id}")
def update_vendor(
    vendor: dict,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    update_vendor_id = vendor.pop("id", None)
    if not update_vendor_id:
        return HTTPException(status_code=400, detail="No vendor ID found in request")
    db.query(models.Vendor).filter(models.Vendor.id == update_vendor_id).update(vendor)
    db.commit()
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"更新供应商信息 {update_vendor_id} {vendor.get('name', '')}", db
    )
    updated_vendor = db.query(models.Vendor).filter(models.Vendor.id == update_vendor_id).first()
    updated_vendor.id = str(updated_vendor.id).rjust(3, '0')
    return updated_vendor


@router.delete("/{vendor_id}")
def delete_vendor(vendor_id: int, db: Session = Depends(get_db)):
    db_vendor_data = vendor_service.get_vendor(vendor_id, db=db)
    if not db_vendor_data:
        raise HTTPException(status_code=400, detail="Matching vendor not found")
    vendor_service.delete_vendor(vendor=db_vendor_data, db=db)
    return JSONResponse(content={"success": True})
