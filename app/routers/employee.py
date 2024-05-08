# coding=utf-8
from fastapi import APIRouter, Depends, Header, Body
from typing import List, Union
from app import models, schemas
from app.services import employee_service, operation_service
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.dependencies import get_db
from datetime import datetime

router = APIRouter(
    prefix="/employee",
    tags=["employee"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Employee])
def read_all_employees(
    db: Session = Depends(get_db),
):
    employees = employee_service.get_all_employees(db=db)
    return employees


@router.get("/{employee_id}", response_model=schemas.Employee)
def read_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = employee_service.get_employee(employee_id=employee_id, db=db)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.get("/name/{name}")
def read_employees_by_name(name: str, db: Session = Depends(get_db)):
    employees = employee_service.get_employees_by_name(name=name, db=db)
    if not employees:
        raise HTTPException(status_code=404, detail="No employee found")
    return employees


@router.get("/phone/{phone}")
def read_employee_by_phone(phone: str, db: Session = Depends(get_db)):
    employee = employee_service.get_employee_by_phone(phone=phone, db=db)
    if not employee:
        raise HTTPException(status_code=404, detail="No employee found")
    return employee


@router.get("/ssn/{ssn}")
def read_employees_by_ssn(ssn: str, db: Session = Depends(get_db)):
    employees = employee_service.get_employees_by_ssn(ssn=ssn, db=db)
    if not employees:
        raise HTTPException(status_code=404, detail="No employee found")
    return employees


@router.get("/department/{department}")
def read_employees_by_department(department: str, db: Session = Depends(get_db)):
    employees = employee_service.get_employees_by_department(
        department=department, db=db
    )
    if not employees:
        raise HTTPException(status_code=404, detail="No employee found")
    return employees


@router.get("/status/{status}")
def read_employees_by_status(status: str, db: Session = Depends(get_db)):
    employees = employee_service.get_employees_by_status(status=status, db=db)
    if not employees:
        raise HTTPException(status_code=404, detail="No employee found")
    return employees


@router.get("/onboard/{after}/{before}")
def read_employees_in_time_range(
    after: datetime, before: datetime, db: Session = Depends(get_db)
):
    employees = employee_service.get_employees_in_onboard_range(
        after=after, before=before, db=db
    )
    if not employees:
        raise HTTPException(status_code=404, detail="No employee found")
    return employees


@router.get("/onboard/{after}/{before}")
def read_employees_in_birthday_range(
    after: datetime, before: datetime, db: Session = Depends(get_db)
):
    employees = employee_service.get_employees_in_birthday_range(
        after=after, before=before, db=db
    )
    if not employees:
        raise HTTPException(status_code=404, detail="No employee found")
    return employees


@router.post("/", response_model=schemas.Employee)
def create_employee(
    employee: schemas.EmployeeCreate,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    new_emp = employee_service.create_employee(employee=employee, db=db)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"创建员工档案 {new_emp.id} {new_emp.name}", db
    )
    return new_emp


@router.put("/last_pay_check")
def update_employee_last_pay_check(
    employee_id: int = Body(...),
    last_pay_check: datetime = Body(...),
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db_employee_data = employee_service.get_employee(employee_id, db=db)
    if not db_employee_data:
        raise HTTPException(status_code=400, detail="Matching employee not found")
    db_employee_model = schemas.Employee(**jsonable_encoder(db_employee_data))
    db_employee_model.last_pay_check = last_pay_check
    updated_emp = employee_service.update_employee(employee=db_employee_model, db=db)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"更新员工信息（工资发放） {updated_emp.id} {updated_emp.name}", db
    )
    return updated_emp


@router.put("/")
def update_employee(
    employee: schemas.Employee,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    # employee status: left / working
    # Prepare update contents
    update_contents = employee.dict(exclude_unset=True)
    update_contents.pop("id", None)
    db.query(models.Employee).filter(models.Employee.id == employee.id).update(
        update_contents
    )
    db.commit()
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"更新员工信息 {employee.id} {employee.name}", db
    )
    return employee


@router.delete("/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    db_employee_data = employee_service.get_employee(employee_id, db=db)
    if not db_employee_data:
        raise HTTPException(status_code=400, detail="Matching employee not found")
    employee_service.delete_employee(employee=db_employee_data, db=db)
    return JSONResponse(content={"success": True})
