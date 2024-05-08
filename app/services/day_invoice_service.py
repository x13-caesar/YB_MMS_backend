from datetime import datetime
from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import schemas
from app.models import DayInvoice, Batch


def filter_out_day_invoice_in_cancelled_batch(
    day_invoices: List[DayInvoice], db: Session
):
    valid_DI = []
    # filter out cancelled batches
    for d in day_invoices:
        batch_status = db.query(Batch.status).filter(Batch.id == d.batch_id).first()
        if batch_status == "cancelled":
            continue
        else:
            valid_DI.append(d)
    return valid_DI


def get_day_invoice(day_invoice_id: int, db: Session):
    return db.query(DayInvoice).filter(DayInvoice.id == day_invoice_id).first()


def get_day_invoices(db: Session):
    return db.query(DayInvoice).all()


def get_day_invoices_by_batch_id(batch_id: int, db: Session):
    return db.query(DayInvoice).filter(DayInvoice.batch_id == batch_id).all()


def get_day_invoices_by_batch_process_id(batch_process_id: int, db: Session):
    return (
        db.query(DayInvoice)
        .filter(DayInvoice.batch_process_id == batch_process_id)
        .all()
    )


def get_day_invoices_by_employee_id(employee_id: int, db: Session):
    return db.query(DayInvoice).filter(DayInvoice.employee_id == employee_id).all()


def get_day_invoices_in_work_date_range(after: datetime, before: datetime, db: Session):
    return (
        db.query(DayInvoice)
        .filter(DayInvoice.work_date >= after, DayInvoice.work_date <= before)
        .all()
    )


def get_day_invoices_by_employee_id_and_work_date_range(
    employee_id: int, after: datetime, before: datetime, db: Session
):
    return (
        db.query(DayInvoice)
        .filter(
            DayInvoice.employee_id == employee_id,
            DayInvoice.work_date >= after,
            DayInvoice.work_date <= before,
        )
        .all()
    )


def get_unchecked_day_invoices_by_employee_id_and_work_date_range(
    employee_id: int, after: datetime, before: datetime, db: Session
):
    return (
        db.query(DayInvoice)
        .filter(
            DayInvoice.employee_id == employee_id,
            DayInvoice.work_date >= after,
            DayInvoice.work_date <= before,
            DayInvoice.check_status == False,
        )
        .all()
    )


def get_day_invoices_by_check_status(check: bool, db: Session):
    return db.query(DayInvoice).filter(DayInvoice.check == check).all()


def create_day_invoice(day_invoice: schemas.DayInvoiceCreate, db: Session):
    new_day_invoice = DayInvoice(**day_invoice.dict())
    db.add(new_day_invoice)
    db.commit()
    db.refresh(new_day_invoice)
    return new_day_invoice


def update_day_invoice(day_invoice: schemas.DayInvoice, db: Session):
    json_day_invoice = jsonable_encoder(day_invoice)
    db_day_invoice = DayInvoice(**json_day_invoice)
    json_day_invoice["check_date"] = json_day_invoice["check_date"][:19]
    db.query(DayInvoice).filter(DayInvoice.id == db_day_invoice.id).update(
        json_day_invoice
    )
    db.commit()
    return db.query(DayInvoice).filter(DayInvoice.id == db_day_invoice.id).first()


def delete_day_invoice(day_invoice: schemas.DayInvoice, db: Session):
    db.query(DayInvoice).filter(DayInvoice.id == day_invoice.id).delete(
        synchronize_session="fetch"
    )
    db.commit()
    return


def get_day_invoices_by_salary_id(salary_id: int, db: Session):
    return db.query(DayInvoice).filter(DayInvoice.salary_id == salary_id).all()


def remove_day_invoices_by_batch_id(
    batch_id: int,
    db: Session,
):
    db.query(DayInvoice).filter(DayInvoice.batch_id == batch_id).delete(
        synchronize_session="fetch"
    )
    return {"success": True}
