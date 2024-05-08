# coding=utf-8
from typing import List, Union

from fastapi import APIRouter, Depends, Header
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app import schemas
from app.dependencies import get_db
from app.services import day_invoice_service, operation_service
from datetime import datetime, timedelta

from app.services.day_invoice_service import filter_out_day_invoice_in_cancelled_batch

router = APIRouter(
    prefix="/day_invoice",
    tags=["day_invoice", "日产记录"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.DayInvoice])
def read_day_invoices(db: Session = Depends(get_db)):
    day_invoices = day_invoice_service.get_day_invoices(db=db)
    return day_invoices


@router.get("/day_invoice_id/{day_invoice_id}", response_model=schemas.DayInvoice)
def read_day_invoice(day_invoice_id: int, db: Session = Depends(get_db)):
    day_invoice = day_invoice_service.get_day_invoice(
        day_invoice_id=day_invoice_id, db=db
    )
    return day_invoice


@router.get("/checked", response_model=List[schemas.DayInvoice])
def read_checked_day_invoices(db: Session = Depends(get_db)):
    return day_invoice_service.get_day_invoices_by_check_status(True, db=db)


@router.get("/unchecked", response_model=List[schemas.DayInvoice])
def read_unchecked_day_invoices(db: Session = Depends(get_db)):
    all_DI = day_invoice_service.get_day_invoices_by_check_status(False, db=db)
    valid_DI = filter_out_day_invoice_in_cancelled_batch(all_DI, db=db)
    return valid_DI


@router.get("/batch_id/{batch_id}")
def read_day_invoices_by_batch_id(batch_id: int, db: Session = Depends(get_db)):
    day_invoices = day_invoice_service.get_day_invoices_by_batch_id(
        batch_id=batch_id, db=db
    )
    return day_invoices


@router.get("/batch_process_id/{batch_process_id}")
def read_day_invoices_by_batch_process_id(
    batch_process_id: int, db: Session = Depends(get_db)
):
    day_invoices = day_invoice_service.get_day_invoices_by_batch_process_id(
        batch_process_id=batch_process_id, db=db
    )
    return day_invoices


@router.get("/employee_id/{employee_id}")
def read_day_invoices_by_employee_id(employee_id: int, db: Session = Depends(get_db)):
    day_invoices = day_invoice_service.get_day_invoices_by_employee_id(
        employee_id=employee_id, db=db
    )
    valid_DI = filter_out_day_invoice_in_cancelled_batch(day_invoices, db=db)
    return valid_DI


@router.get("/work_date/{after}/{before}")
def read_day_invoices_in_work_date_range(
    after: datetime, before: datetime, db: Session = Depends(get_db)
):
    day_invoices = day_invoice_service.get_day_invoices_in_work_date_range(
        after=after, before=before, db=db
    )
    valid_DI = filter_out_day_invoice_in_cancelled_batch(day_invoices, db=db)
    return valid_DI


# All datetime passed by path params should be in format "YYYY-MM-DD"
@router.get("/employee_id_and_work_date/{employee_id}/{after}/{before}")
def read_day_invoices_by_employee_id_and_work_date_range(
    employee_id: int, after: datetime, before: datetime, db: Session = Depends(get_db)
):
    day_invoices = (
        day_invoice_service.get_day_invoices_by_employee_id_and_work_date_range(
            employee_id=employee_id, after=after, before=before, db=db
        )
    )
    valid_DI = filter_out_day_invoice_in_cancelled_batch(day_invoices, db=db)
    return valid_DI


@router.get("/unchecked/employee_id_and_work_date/{employee_id}/{after}/{before}")
def read_unchecked_day_invoices_by_employee_id_and_work_date_range(
    employee_id: int, after: datetime, before: datetime, db: Session = Depends(get_db)
):
    day_invoices = day_invoice_service.get_unchecked_day_invoices_by_employee_id_and_work_date_range(
        employee_id=employee_id, after=after, before=before, db=db
    )
    valid_DI = filter_out_day_invoice_in_cancelled_batch(day_invoices, db=db)
    return valid_DI


@router.get("/salary_id/{salary_id}")
def read_day_invoices_by_salary_id(salary_id: int, db: Session = Depends(get_db)):
    return day_invoice_service.get_day_invoices_by_salary_id(salary_id=salary_id, db=db)


@router.post("/", response_model=schemas.DayInvoice)
def create_day_invoice(
    day_invoice: schemas.DayInvoiceCreate,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    new_day_invoice = day_invoice_service.create_day_invoice(
        day_invoice=day_invoice, db=db
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"创建新日产记录：批次{new_day_invoice.batch_id}|日期{new_day_invoice.work_date}|员工{new_day_invoice.employee_name}",
        db,
    )
    return new_day_invoice


@router.put("/", response_model=schemas.DayInvoice)
def update_day_invoice(
    day_invoice: schemas.DayInvoice,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db_day_invoice_data = day_invoice_service.get_day_invoice(day_invoice.id, db=db)
    db_day_invoice_model = schemas.DayInvoice(**jsonable_encoder(db_day_invoice_data))
    update_data = day_invoice.dict(exclude_unset=True)
    updated_day_invoice = day_invoice_service.update_day_invoice(
        day_invoice=db_day_invoice_model.copy(update=update_data), db=db
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"更新日产记录：批次{updated_day_invoice.batch_id}|日期{updated_day_invoice.work_date}|员工{updated_day_invoice.employee_name}",
        db,
    )
    return updated_day_invoice


@router.delete("/{day_invoice_id}")
def delete_day_invoice(day_invoice_id: int, db: Session = Depends(get_db)):
    db_day_invoice_data = day_invoice_service.get_day_invoice(day_invoice_id, db=db)
    day_invoice_service.delete_day_invoice(day_invoice=db_day_invoice_data, db=db)
    return JSONResponse(content={"success": True})
