from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app import schemas, models


def get_buyer(buyer_id: int, db: Session):
    return db.query(models.Buyer).filter(models.Buyer.id == buyer_id).first()


def get_buyers(db: Session):
    return db.query(models.Buyer).all()


def get_buyer_by_company(company: str, db: Session):
    return db.query(models.Buyer).filter(models.Buyer.company == company).first()


def get_buyer_by_name(name: str, db: Session):
    return db.query(models.Buyer).filter(models.Buyer.name == name).all()


def create_buyer(buyer: schemas.BuyerCreate, db: Session):
    new_buyer = models.Buyer(**buyer.dict())
    db.add(new_buyer)
    db.commit()
    db.refresh(new_buyer)
    return new_buyer


def update_buyer(buyer: schemas.Buyer, db: Session):
    updated_buyer = models.Buyer(**buyer.dict())
    db.query(models.Buyer).filter(models.Buyer.id == updated_buyer.id).update(
        jsonable_encoder(updated_buyer)
    )
    db.commit()
    return db.query(models.Buyer).filter(models.Buyer.id == updated_buyer.id).first()


def delete_buyer(buyer: schemas.Buyer, db: Session):
    db.query(models.Buyer).filter(models.Buyer.id == buyer.id).delete(
        synchronize_session="fetch"
    )
    db.commit()
    return
