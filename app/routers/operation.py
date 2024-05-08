# coding=utf-8
from fastapi import APIRouter, Depends
from typing import List
from app import models, schemas
from app.services import operation_service
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.dependencies import get_db
from datetime import datetime

router = APIRouter(
    prefix="/operation",
    tags=["operation"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Operation])
def read_operations(db: Session = Depends(get_db)):
    # Automatically remove all operations from over 6 months ago
    operation_service.delete_expired_operations(db=db)
    # Get the rest of the operations.
    operations = operation_service.get_operations(db=db)
    return operations


@router.get("/recent", response_model=List[schemas.Operation])
def read_recent_operations(db: Session = Depends(get_db)):
    operations = (
        db.query(models.Operation)
        .order_by(desc(models.Operation.execute_time))
        .limit(20)
        .all()
    )
    return operations


@router.get("/{operation_id}", response_model=schemas.Operation)
def read_operation(operation_id: int, db: Session = Depends(get_db)):
    operation = operation_service.get_operation(operation_id=operation_id, db=db)
    if operation is None:
        raise HTTPException(status_code=404, detail="Operation not found")
    return operation


@router.get("/operator/{operator}")
def read_operations_by_operator(operator: str, db: Session = Depends(get_db)):
    operations = operation_service.get_operations_by_operator(operator=operator, db=db)
    if not operations:
        raise HTTPException(status_code=404, detail="No operation found")
    return operations


@router.get("/execute_time/{after}/{before}")
def read_operations_in_time_range(
    after: datetime, before: datetime, db: Session = Depends(get_db)
):
    operations = operation_service.get_operations_in_time_range(
        after=after, before=before, db=db
    )
    if not operations:
        raise HTTPException(status_code=404, detail="No operation found")
    return operations


@router.post("/", response_model=schemas.Operation)
def create_operation(operation: schemas.OperationCreate, db: Session = Depends(get_db)):
    return operation_service.create_operation(operation=operation, db=db)


@router.put("/")
def update_operation(operation: schemas.Operation, db: Session = Depends(get_db)):
    db_operation_data = operation_service.get_operation(operation.id, db=db)
    if not db_operation_data:
        raise HTTPException(status_code=400, detail="Matching operation not found")
    db_operation_model = schemas.Operation(**jsonable_encoder(db_operation_data))
    update_data = operation.dict(exclude_unset=True)
    updated_operation = db_operation_model.copy(update=update_data)
    return operation_service.update_operation(operation=updated_operation, db=db)


@router.delete("/{operation_id}")
def delete_operation(operation_id: int, db: Session = Depends(get_db)):
    db_operation_data = operation_service.get_operation(operation_id, db=db)
    if not db_operation_data:
        raise HTTPException(status_code=400, detail="Matching operation not found")
    operation_service.delete_operation(operation=db_operation_data, db=db)
    return JSONResponse(content={"success": True})
