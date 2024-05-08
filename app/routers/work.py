# coding=utf-8
from fastapi import APIRouter, Depends, Header
from typing import List, Union

from app import models, schemas
from app.services import work_service, operation_service
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.dependencies import get_db
from datetime import datetime

router = APIRouter(
    prefix="/work",
    tags=["work", "工单"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Work])
def read_works(db: Session = Depends(get_db)):
    works = work_service.get_works(db=db)
    return works


@router.get("/work_id/{work_id}", response_model=schemas.Work)
def read_work(work_id: int, db: Session = Depends(get_db)):
    work = work_service.get_work(work_id=work_id, db=db)
    return work


@router.get("/checked", response_model=List[schemas.Work])
def read_checked_works(db: Session = Depends(get_db)):
    return work_service.get_works_by_check_status(True, db=db)


@router.get("/unchecked", response_model=List[schemas.Work])
def read_unchecked_works(db: Session = Depends(get_db)):
    return work_service.get_works_by_check_status(False, db=db)


@router.get("/batch_process_id/{batch_process_id}")
def read_works_by_batch_process_id(
    batch_process_id: int, db: Session = Depends(get_db)
):
    works = work_service.get_works_by_batch_process_id(
        batch_process_id=batch_process_id, db=db
    )
    return works


@router.get("/employee_id/{employee_id}")
def read_works_by_employee_id(employee_id: int, db: Session = Depends(get_db)):
    works = work_service.get_works_by_employee_id(employee_id=employee_id, db=db)
    return works


@router.get("/work_date/{after}/{before}")
def read_works_in_work_date_range(
    after: datetime, before: datetime, db: Session = Depends(get_db)
):
    works = work_service.get_works_in_work_date_range(after=after, before=before, db=db)
    return works


# All datetime passed by path params should be in format "YYYY-MM-DD"
@router.get("/employee_id_and_work_date/{employee_id}/{after}/{before}")
def read_works_by_employee_id_and_work_date_range(
    employee_id: int, after: datetime, before: datetime, db: Session = Depends(get_db)
):
    works = work_service.get_works_by_employee_id_and_work_date_range(
        employee_id=employee_id, after=after, before=before, db=db
    )
    return works


@router.get("/unchecked/employee_id_and_work_date/{employee_id}/{after}/{before}")
def read_unchecked_works_by_employee_id_and_work_date_range(
    employee_id: int, after: datetime, before: datetime, db: Session = Depends(get_db)
):
    works = work_service.get_unchecked_works_by_employee_id_and_work_date_range(
        employee_id=employee_id, after=after, before=before, db=db
    )
    return works


@router.post("/", response_model=schemas.Work)
def create_work(
    work: schemas.WorkCreate,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    new_work = work_service.create_work(work=work, db=db)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"创建新工单 {new_work.employee_name} {new_work.work_date}", db
    )
    return new_work


@router.put("/", response_model=schemas.Work)
def update_work(
    work: schemas.Work,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db_work_data = work_service.get_work(work.id, db=db)
    if not db_work_data:
        raise HTTPException(status_code=400, detail="Matching work not found")
    db_work_model = schemas.Work(**jsonable_encoder(db_work_data))
    update_data = work.dict(exclude_unset=True)
    updated_work = work_service.update_work(
        work=db_work_model.copy(update=update_data), db=db
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"更新工单信息 {updated_work.employee_name} {updated_work.work_date}",
        db,
    )
    return updated_work


@router.delete("/{work_id}")
def delete_work(work_id: int, db: Session = Depends(get_db)):
    db_work_data = work_service.get_work(work_id, db=db)
    if not db_work_data:
        raise HTTPException(status_code=400, detail="Matching work not found")
    db.query(models.WorkSpecification).filter(
        models.WorkSpecification.work_id == work_id
    ).delete(synchronize_session="fetch")
    db.query(models.Work).filter(models.Work.id == work_id).delete(
        synchronize_session="fetch"
    )
    db.commit()
    return JSONResponse(content={"success": True})
