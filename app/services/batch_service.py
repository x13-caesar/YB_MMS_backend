from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder

from app.models import Batch, Product

from datetime import datetime

from app import schemas
from app.services import product_service


def get_batch(batch_id: int, db: Session):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    batch.product_name = str(
        db.query(Product.name).filter(Product.id == batch.product_id).first()[0]
    )
    return batch


def get_batch_meta_info(batch_id: int, db: Session):
    return (
        db.query(
            Batch.id,
            Batch.status,
            Batch.product_id,
            Batch.plan_amount,
            Batch.actual_amount,
            Batch.create,
            Batch.start,
            Batch.end,
            Batch.ship,
            Batch.notice,
        )
        .filter(Batch.id == batch_id)
        .first()
    )


def get_batches(db: Session):
    return db.query(Batch).all()


def get_batches_in_month(year: int, month: int, db: Session):
    lower_bound = ((year - 2000) * 100 + month) * 100
    upper_bound = lower_bound + 100
    return db.query(Batch).filter(Batch.id > lower_bound, Batch.id < upper_bound).all()


def get_batches_meta_info(db: Session):
    return db.query(
        Batch.id,
        Batch.status,
        Batch.product_id,
        Batch.plan_amount,
        Batch.actual_amount,
        Batch.create,
        Batch.start,
        Batch.end,
        Batch.ship,
        Batch.notice,
    ).all()


def get_batches_by_status(status: str, db: Session):
    batches = db.query(Batch).filter(Batch.status == status).all()
    for b in batches:
        b.product_name = product_service.get_product_name(
            product_id=b.product_id, db=db
        )
    return batches


def get_batches_by_product_id(product_id: str, db: Session):
    return db.query(Batch).filter(Batch.product_id == product_id).all()


def get_batches_by_product_id_and_status(product_id: str, status: str, db: Session):
    return (
        db.query(Batch)
        .filter(Batch.product_id == product_id, Batch.status == status)
        .all()
    )


def get_batches_plan_amount_over(amount: int, db: Session):
    return db.query(Batch).filter(Batch.plan_amount >= amount).all()


def get_batches_plan_amount_equal(amount: int, db: Session):
    return db.query(Batch).filter(Batch.plan_amount == amount).all()


def get_batches_plan_amount_under(amount: int, db: Session):
    return db.query(Batch).filter(Batch.plan_amount <= amount).all()


def get_batches_not_fulfilled(db: Session):
    return db.query(Batch).filter(Batch.actual_amount < Batch.plan_amount).all()


def get_batches_start_after(date: datetime, db: Session):
    return db.query(Batch).filter(Batch.start >= date).all()


def get_batches_start_on(date: datetime, db: Session):
    return db.query(Batch).filter(Batch.start == date).all()


def get_batches_start_before(date: datetime, db: Session):
    return db.query(Batch).filter(Batch.start <= date).all()


def get_batches_end_after(date: datetime, db: Session):
    return db.query(Batch).filter(Batch.end >= date).all()


def get_batches_ship_after(date: datetime, db: Session):
    return db.query(Batch).filter(Batch.ship >= date).all()


def get_batches_ship_on(date: datetime, db: Session):
    return db.query(Batch).filter(Batch.ship == date).all()


def get_batches_ship_before(date: datetime, db: Session):
    return db.query(Batch).filter(Batch.ship <= date).all()


def update_batch(batch: schemas.Batch, db: Session):
    json_batch = jsonable_encoder(batch)
    json_batch.pop("batch_process", None)
    json_batch.pop("product_name", None)
    updated_batch = Batch(**json_batch)
    db.query(Batch).filter(Batch.id == updated_batch.id).update(
        jsonable_encoder(updated_batch)
    )
    db.commit()
    return db.query(Batch).filter(Batch.id == updated_batch.id).first()


def delete_batch(batch: schemas.Batch, db: Session):
    db.query(Batch).filter(Batch.id == batch.id).delete(synchronize_session="fetch")
    db.commit()
    return
