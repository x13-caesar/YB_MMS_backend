# coding=utf-8
from fastapi import APIRouter, Depends, Header
from typing import List, Union

from app import models, schemas
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.dependencies import get_db

router = APIRouter(
    prefix="/product_category",
    tags=["products", "category", "产品"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.ProductCategory])
def read_product_categories(db: Session = Depends(get_db)):
    products = db.query(models.ProductCategory).all()
    return products


@router.post("/")
def create_product_category(
    product_category: schemas.ProductCategoryCreate,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    data = jsonable_encoder(product_category)
    new = models.ProductCategory(**data)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new
