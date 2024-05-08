from fastapi import APIRouter, Depends
from typing import List
from app import schemas
from app.services import process_component_service, process_service
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.dependencies import get_db

router = APIRouter(
    prefix="/process_component",
    tags=["process_component"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.ProcessComponent])
def read_process_components(db: Session = Depends(get_db)):
    process_components = process_component_service.get_process_components(db=db)
    return process_components


@router.get("/{process_component_id}", response_model=schemas.ProcessComponent)
def read_process_component(process_component_id: int, db: Session = Depends(get_db)):
    process_component = process_component_service.get_process_component(
        process_component_id=process_component_id, db=db
    )
    if process_component is None:
        raise HTTPException(status_code=404, detail="Process component not found")
    return process_component


@router.get("/process_id/{process_id}")
def read_process_components_by_process_id(
    process_id: str, db: Session = Depends(get_db)
):
    process_components = process_component_service.get_process_components_by_process_id(
        process_id=process_id, db=db
    )
    if not process_components:
        raise HTTPException(status_code=404, detail="No process component found")
    return process_components


@router.get("/component_id/{component_id}")
def read_process_components_by_component_id(
    component_id: str, db: Session = Depends(get_db)
):
    process_components = (
        process_component_service.get_process_components_by_component_id(
            component_id=component_id, db=db
        )
    )
    if not process_components:
        raise HTTPException(status_code=404, detail="No process component found")
    return process_components


@router.get("/product_id/{product_id}")
def read_process_components_by_product_id(
    product_id: str, db: Session = Depends(get_db)
):
    processes = process_service.get_processes_by_product_id(
        product_id=product_id, db=db
    )
    result = []
    for process in processes:
        process_components = (
            process_component_service.get_process_components_by_process_id(
                process_id=process.id, db=db
            )
        )
        if process_components:
            result.extend(result)
    if not result:
        raise HTTPException(status_code=404, detail="No process component found")
    return result


@router.post("/", response_model=schemas.ProcessComponent)
def create_process_component(
    process_component: schemas.ProcessComponentCreate, db: Session = Depends(get_db)
):
    return process_component_service.create_process_component(
        process_component=process_component, db=db
    )


@router.put("/")
def update_process_component(
    process_component: schemas.ProcessComponent, db: Session = Depends(get_db)
):
    db_process_component_data = process_component_service.get_process_component(
        process_component.id, db=db
    )
    if not db_process_component_data:
        raise HTTPException(
            status_code=400, detail="Matching process component not found"
        )
    db_process_component_model = schemas.ProcessComponent(
        **jsonable_encoder(db_process_component_data)
    )
    update_data = process_component.dict(exclude_unset=True)
    updated_process_component = db_process_component_model.copy(update=update_data)
    return process_component_service.update_process_component(
        process_component=updated_process_component, db=db
    )


@router.delete("/{process_component_id}")
def delete_process_component(process_component_id: int, db: Session = Depends(get_db)):
    db_process_component_data = process_component_service.get_process_component(
        process_component_id, db=db
    )
    if not db_process_component_data:
        raise HTTPException(
            status_code=400, detail="Matching process component not found"
        )
    process_component_service.delete_process_component(
        process_component=db_process_component_data, db=db
    )
    return JSONResponse(content={"success": True})
