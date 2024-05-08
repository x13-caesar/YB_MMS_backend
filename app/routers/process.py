from fastapi import APIRouter, Depends
from typing import List
from app import schemas
from app.services import process_service
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.dependencies import get_db

router = APIRouter(
    prefix="/process",
    tags=["process"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Process])
def read_processes(db: Session = Depends(get_db)):
    processes = process_service.get_processes(db=db)
    return processes


@router.get("/{process_id}", response_model=schemas.Process)
def read_process(process_id: str, db: Session = Depends(get_db)):
    process = process_service.get_process(process_id=process_id, db=db)
    if process is None:
        raise HTTPException(status_code=404, detail="Process not found")
    return process


@router.get("/product_id/{product_id}", response_model=List[schemas.Process])
def read_processes_by_product_id(product_id: str, db: Session = Depends(get_db)):
    processes = process_service.get_processes_by_product_id(
        product_id=product_id, db=db
    )
    if not processes:
        raise HTTPException(status_code=404, detail="No process found")
    return processes


@router.get("/name/{name}")
def read_processes_by_name(name: str, db: Session = Depends(get_db)):
    processes = process_service.get_processes_by_name(name=name, db=db)
    if not processes:
        raise HTTPException(status_code=404, detail="No process found")
    return processes


@router.post("/", response_model=schemas.Process)
def create_process(process: schemas.ProcessCreate, db: Session = Depends(get_db)):
    return process_service.create_process(process=process, db=db)


@router.put("/")
def update_process(process: schemas.Process, db: Session = Depends(get_db)):
    db_process_data = process_service.get_process(process.id, db=db)
    if not db_process_data:
        raise HTTPException(status_code=400, detail="Matching process not found")
    db_process_model = schemas.Process(**jsonable_encoder(db_process_data))
    update_data = process.dict(exclude_unset=True)
    updated_process = db_process_model.copy(update=update_data)
    return process_service.update_process(process=updated_process, db=db)


@router.delete("/{process_id}")
def delete_process(process_id: str, db: Session = Depends(get_db)):
    db_process_data = process_service.get_process(process_id, db=db)
    if not db_process_data:
        raise HTTPException(status_code=400, detail="Matching process not found")
    process_service.delete_process(process=db_process_data, db=db)
    return JSONResponse(content={"success": True})
