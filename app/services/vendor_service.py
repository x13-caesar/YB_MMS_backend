from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app import schemas, models


def get_vendor(vendor_id: int, db: Session):
    return db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()


def get_vendors(db: Session):
    return db.query(models.Vendor).all()


def get_vendor_by_company(company: str, db: Session):
    return db.query(models.Vendor).filter(models.Vendor.company == company).first()


def get_vendor_by_name(name: str, db: Session):
    return db.query(models.Vendor).filter(models.Vendor.name == name).all()


def create_vendor(vendor: schemas.VendorCreate, db: Session):
    new_vendor = models.Vendor(**vendor.dict())
    db.add(new_vendor)
    db.flush()
    db.refresh(new_vendor)
    return new_vendor


def update_vendor(vendor: schemas.Vendor, db: Session):
    updated_vendor = models.Vendor(**vendor.dict())
    db.query(models.Vendor).filter(models.Vendor.id == updated_vendor.id).update(
        jsonable_encoder(updated_vendor)
    )
    db.commit()
    return db.query(models.Vendor).filter(models.Vendor.id == updated_vendor.id).first()


def delete_vendor(vendor: schemas.Vendor, db: Session):
    db.query(models.Vendor).filter(models.Vendor.id == vendor.id).delete(
        synchronize_session="fetch"
    )
    db.commit()
    return
