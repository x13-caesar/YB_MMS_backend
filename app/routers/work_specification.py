from fastapi import APIRouter, Depends
from typing import List
from app import schemas
from app.services import work_specification_service, work_service, batch_process_service
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.dependencies import get_db

router = APIRouter(
    prefix="/work_specification",
    tags=["work_specification"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.WorkSpecification])
def read_work_specifications(db: Session = Depends(get_db)):
    work_specifications = work_specification_service.get_work_specifications(db=db)
    return work_specifications


@router.get("/{work_specification_id}", response_model=schemas.WorkSpecification)
def read_work_specification(work_specification_id: int, db: Session = Depends(get_db)):
    work_specification = work_specification_service.get_work_specification(
        work_specification_id=work_specification_id, db=db
    )
    if work_specification is None:
        raise HTTPException(status_code=404, detail="WorkSpecification not found")
    return work_specification


@router.get("/work_id/{work_id}")
def read_work_specifications_by_work_id(work_id: int, db: Session = Depends(get_db)):
    work_specifications = work_specification_service.get_work_specifications_by_work_id(
        work_id=work_id, db=db
    )
    if not work_specifications:
        raise HTTPException(status_code=404, detail="No work_specification found")
    return work_specifications


@router.get("/specification_id/{specification_id}")
def read_work_specifications_by_specification_id(
    specification_id: int, db: Session = Depends(get_db)
):
    work_specifications = (
        work_specification_service.get_work_specifications_by_specification_id(
            specification_id=specification_id, db=db
        )
    )
    if not work_specifications:
        raise HTTPException(status_code=404, detail="No work_specification found")
    return work_specifications


@router.get("/not_fulfilled", response_model=List[schemas.WorkSpecification])
def read_work_specifications_not_fulfilled(db: Session = Depends(get_db)):
    return work_specification_service.get_work_specifications_not_fulfilled(db=db)


@router.get("/batch_id/{batch_id}", response_model=List[schemas.WorkSpecification])
def read_work_specifications_by_batch_id(batch_id: int, db: Session = Depends(get_db)):
    batch_processes = batch_process_service.get_batch_processes_by_batch_id(
        batch_id=batch_id, db=db
    )
    total_works, total_work_specifications = [], []
    for bp in batch_processes:
        bp_works = work_service.get_works_by_batch_process_id(
            batch_process_id=bp.id, db=db
        )
        if bp_works:
            total_works.extend(bp_works)
    for work in total_works:
        work_specification = (
            work_specification_service.get_work_specifications_by_work_id(
                work_id=work.id, db=db
            )
        )
        if work_specification:
            total_work_specifications.extend(work_specification)
    return total_work_specifications


@router.post("/", response_model=schemas.WorkSpecification)
def create_work_specification(
    work_specification: schemas.WorkSpecificationCreate, db: Session = Depends(get_db)
):
    return work_specification_service.create_work_specification(
        work_specification=work_specification, db=db
    )


@router.put("/")
def update_work_specification(
    work_specification: schemas.WorkSpecification, db: Session = Depends(get_db)
):
    db_work_specification_data = work_specification_service.get_work_specification(
        work_specification.id, db=db
    )
    if not db_work_specification_data:
        raise HTTPException(
            status_code=400, detail="Matching work_specification not found"
        )
    db_work_specification_model = schemas.WorkSpecification(
        **jsonable_encoder(db_work_specification_data)
    )
    update_data = work_specification.dict(exclude_unset=True)
    updated_work_specification = db_work_specification_model.copy(update=update_data)
    return work_specification_service.update_work_specification(
        work_specification=updated_work_specification, db=db
    )


@router.delete("/{work_specification_id}")
def delete_work_specification(
    work_specification_id: int, db: Session = Depends(get_db)
):
    db_work_specification_data = work_specification_service.get_work_specification(
        work_specification_id, db=db
    )
    if not db_work_specification_data:
        raise HTTPException(
            status_code=400, detail="Matching work_specification not found"
        )
    work_specification_service.delete_work_specification(
        work_specification=db_work_specification_data, db=db
    )
    return JSONResponse(content={"success": True})
