# coding=utf-8

from datetime import datetime
from typing import List, Union

from fastapi import APIRouter, Depends, Header
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import schemas, models
from app.dependencies import get_db
from app.services import delivery_service, operation_service, product_service

router = APIRouter(
    prefix="/delivery",
    tags=["delivery"],
    responses={404: {"description": "Not found"}},
)


@router.get("/all", response_model=List[schemas.Delivery])
def read_deliveries(db: Session = Depends(get_db)):
    deliveries = delivery_service.get_deliveries(db=db)
    return deliveries


@router.get("/", response_model=schemas.Delivery)
def read_delivery(delivery_id: int, db: Session = Depends(get_db)):
    delivery = delivery_service.get_delivery(delivery_id=delivery_id, db=db)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery


@router.get("/product_id/{product_id}")
def read_deliveries_by_product_id(product_id: str, db: Session = Depends(get_db)):
    deliveries = delivery_service.get_deliveries_by_product_id(
        product_id=product_id, db=db
    )
    if not deliveries:
        raise HTTPException(status_code=404, detail="No delivery found")
    return deliveries


@router.get("/buyer_id/{buyer_id}")
def read_deliveries_by_buyer_id(buyer_id: int, db: Session = Depends(get_db)):
    deliveries = delivery_service.get_deliveries_by_buyer_id(buyer_id=buyer_id, db=db)
    if not deliveries:
        raise HTTPException(status_code=404, detail="No delivery found")
    return deliveries


@router.get("/order_id/{order_id}")
def read_deliveries_by_order_id(order_id: str, db: Session = Depends(get_db)):
    delivery = delivery_service.get_delivery_by_order_id(order_id=order_id, db=db)
    if not delivery:
        raise HTTPException(status_code=404, detail="No delivery found")
    return delivery


@router.get("/range")
def read_deliveries_in_time_range(start: str, end: str, db: Session = Depends(get_db)):
    deliveries = delivery_service.get_deliveries_in_time_range(
        after=datetime.strptime(start, "%Y-%m-%d"),
        before=datetime.strptime(end, "%Y-%m-%d"),
        db=db,
    )
    return deliveries


@router.get("/total_price/{lower_bound}/{upper_bound}")
def read_deliveries_in_total_price_range(
        lower_bound: int, upper_bound: int, db: Session = Depends(get_db)
):
    deliveries = delivery_service.get_deliveries_in_total_price_range(
        lower_bound=lower_bound, upper_bound=upper_bound, db=db
    )
    if not deliveries:
        raise HTTPException(status_code=404, detail="No delivery found")
    return deliveries


@router.get("/amount/{lower_bound}/{upper_bound}")
def read_deliveries_in_amount_range(
        lower_bound: int, upper_bound: int, db: Session = Depends(get_db)
):
    deliveries = delivery_service.get_deliveries_in_amount_range(
        lower_bound=lower_bound, upper_bound=upper_bound, db=db
    )
    if not deliveries:
        raise HTTPException(status_code=404, detail="No delivery found")
    return deliveries


@router.post("/", response_model=schemas.Delivery)
def create_delivery(
        delivery: schemas.DeliveryCreate,
        authorization: Union[str, None] = Header(default=None),
        db: Session = Depends(get_db),
):
    new_delivery = delivery_service.create_delivery(delivery=delivery, db=db)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"创建交付记录 {new_delivery.product_id} @ {new_delivery.deliver_date}",
        db,
    )
    product_service.change_product_inventory(
        product_id=delivery.product_id, adjust=-delivery.amount, db=db
    )
    return new_delivery


@router.put("/")
def update_delivery(
        delivery: schemas.Delivery,
        authorization: Union[str, None] = Header(default=None),
        db: Session = Depends(get_db),
):
    updated_delivery = delivery_service.update_delivery(delivery=delivery, db=db)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"更新交付记录 {updated_delivery.product_id} @ {updated_delivery.deliver_date}",
        db,
    )
    return updated_delivery


@router.put("/status-change")
def make_delivery_status_change(id: int, reconciled: bool = None, paid: bool = None,
                                authorization: Union[str, None] = Header(default=None),
                                db: Session = Depends(get_db)):
    if paid is not None:
        db.query(models.Delivery).filter(models.Delivery.id == id).update({'paid': paid})
    if reconciled is not None:
        db.query(models.Delivery).filter(models.Delivery.id == id).update({'reconciled': reconciled})
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"更新交付记录 {id} 的状态",
        db,
    )
    return {'success': True, 'reconciled': reconciled, 'paid': paid}


@router.delete("/{delivery_id}")
def delete_delivery(
        delivery_id: int,
        authorization: Union[str, None] = Header(default=None),
        db: Session = Depends(get_db),
):
    db_delivery_data = delivery_service.get_delivery(delivery_id, db=db)
    if not db_delivery_data:
        return HTTPException(status_code=500, detail="Matching delivery not found")
    delivery_service.delete_delivery(delivery_id=delivery_id, db=db)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"删除交付记录 {db_delivery_data.product_id} @ {db_delivery_data.deliver_date}",
        db,
    )
    return JSONResponse(content={"success": True})
