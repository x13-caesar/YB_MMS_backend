# coding=utf-8
from enum import Enum

from fastapi import APIRouter, Depends, Header
from typing import List, Union

from app import models, schemas
from app.services import (
    batch_process_service,
    batch_service,
    specification_service,
    operation_service,
)
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.dependencies import get_db

router = APIRouter(
    prefix="/batch_process",
    tags=["batch_process"],
    responses={404: {"description": "Not found"}},
)


class BatchProcessStatus(str, Enum):
    unstarted = "unstarted"
    ongoing = "ongoing"
    finished = "finished"


@router.get("/", response_model=List[schemas.BatchProcess])
def read_batch_processes(db: Session = Depends(get_db)):
    batch_processes = batch_process_service.get_batch_processes(db=db)
    return batch_processes


@router.get("/{batch_process_id}", response_model=schemas.BatchProcess)
def read_batch_process(batch_process_id: int, db: Session = Depends(get_db)):
    batch_process = batch_process_service.get_batch_process(
        batch_process_id=batch_process_id, db=db
    )
    if batch_process is None:
        raise HTTPException(status_code=404, detail="Process component not found")
    return batch_process


@router.get("/batch_id/{batch_id}", response_model=List[schemas.BatchProcess])
def read_batch_process(batch_id: int, db: Session = Depends(get_db)):
    batch_processes = batch_process_service.get_batch_processes_by_batch_id(
        batch_id=batch_id, db=db
    )
    if batch_processes is None:
        raise HTTPException(status_code=404, detail="Process component not found")
    return batch_processes


@router.get("/process_id/{process_id}")
def read_batch_processes_by_process_id(process_id: str, db: Session = Depends(get_db)):
    batch_processes = batch_process_service.get_batch_processes_by_process_id(
        process_id=process_id, db=db
    )
    if not batch_processes:
        raise HTTPException(status_code=404, detail="No process component found")
    return batch_processes


@router.get("/status/{status}")
def read_batch_processes_by_status(status: str, db: Session = Depends(get_db)):
    batch_processes = batch_process_service.get_batch_processes_by_status(
        status=status, db=db
    )
    if not batch_processes:
        raise HTTPException(status_code=404, detail="No process component found")
    return batch_processes


@router.get("/product_id/{product_id}/{batch_status}")
def read_batch_processes_by_product_id_and_batch_status(
    product_id: str, batch_status: str, db: Session = Depends(get_db)
):
    batches = batch_service.get_batches_by_product_id_and_status(
        product_id=product_id, status=batch_status, db=db
    )
    result = []
    for batch in batches:
        batch_processes = batch_process_service.get_batch_processes_by_batch_id(
            batch_id=batch.id, db=db
        )
        if batch_processes:
            result.extend(result)
    if not result:
        raise HTTPException(status_code=404, detail="No process component found")
    return result


@router.post("/", response_model=schemas.BatchProcess)
def create_batch_process(
    batch_process: schemas.BatchProcessCreate, db: Session = Depends(get_db)
):
    return batch_process_service.create_batch_process(
        batch_process=batch_process, db=db
    )


@router.put("/")
def update_batch_process(
    batch_process: schemas.BatchProcess, db: Session = Depends(get_db)
):
    db_batch_process_data = batch_process_service.get_batch_process(
        batch_process.id, db=db
    )
    if not db_batch_process_data:
        raise HTTPException(
            status_code=400, detail="Matching process component not found"
        )
    db_batch_process_model = schemas.BatchProcess(
        **jsonable_encoder(db_batch_process_data)
    )
    update_data = batch_process.dict(exclude_unset=True)
    updated_batch_process = db_batch_process_model.copy(update=update_data)
    return batch_process_service.update_batch_process(
        batch_process=updated_batch_process, db=db
    )


@router.put("/finish")
def finish_batch_process(
    bp: schemas.BatchProcess,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    # update batch process (end_amount)
    sum_amount = sum([int(w.complete_unit) for w in bp.work])
    db.query(models.BatchProcess).filter(models.BatchProcess.id == bp.id).update(
        {"end_amount": sum_amount, "status": BatchProcessStatus.finished.value}
    )
    # 创建新工单 / 更新工单
    for w in bp.work:
        existing_work = db.query(models.Work).filter(
            models.Work.batch_process_id == bp.id,
            models.Work.employee_id == w.employee_id,
        )
        # there was work with same process and employee => update it
        if existing_work.first():
            existing_work.update(w.dict())
        # no previous corresponding work => insert new work
        else:
            new_work = models.Work(**w.dict())
            db.add(new_work)
    # 更新配件库存
    for wr in bp.warehouse_record:
        spec_id = wr.specification_id
        spec_consumption = wr.consumption * sum_amount
        db_spec = specification_service.get_specification(
            specification_id=spec_id, db=db
        )
        db_spec.stock -= spec_consumption
        specification_service.update_specification(specification=db_spec, db=db)
    db.commit()
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"更新生产工艺进度 {bp.id}", db
    )
    return db.query(models.BatchProcess).filter(models.BatchProcess.id == bp.id).first()


@router.delete("/{batch_process_id}")
def delete_batch_process(batch_process_id: int, db: Session = Depends(get_db)):
    db_batch_process_data = batch_process_service.get_batch_process(
        batch_process_id, db=db
    )
    if not db_batch_process_data:
        raise HTTPException(
            status_code=400, detail="Matching process component not found"
        )
    batch_process_service.delete_batch_process(
        batch_process=db_batch_process_data, db=db
    )
    return JSONResponse(content={"success": True})
