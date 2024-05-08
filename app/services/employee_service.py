from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app import schemas, models

from datetime import datetime


def get_employee(employee_id: int, db: Session):
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()


def get_all_employees(db: Session):
    return db.query(models.Employee).all()


def get_employees_by_name(name: str, db: Session):
    return db.query(models.Employee).filter(models.Employee.name == name).all()


def get_employee_by_phone(phone: str, db: Session):
    return db.query(models.Employee).filter(models.Employee.phone == phone).first()


def get_employees_by_ssn(ssn: str, db: Session):
    return db.query(models.Employee).filter(models.Employee.ssn == ssn).all()


def get_employees_by_department(department: str, db: Session):
    return (
        db.query(models.Employee).filter(models.Employee.department == department).all()
    )


def get_employees_by_status(status: str, db: Session):
    return db.query(models.Employee).filter(models.Employee.status == status).all()


def get_employees_in_birthday_range(after: datetime, before: datetime, db: Session):
    return (
        db.query(models.Employee)
        .filter(models.Employee.birth >= after, models.Employee.birth <= before)
        .all()
    )


def get_employees_in_onboard_range(after: datetime, before: datetime, db: Session):
    return (
        db.query(models.Employee)
        .filter(models.Employee.onboard >= after, models.Employee.onboard <= before)
        .all()
    )


def create_employee(employee: schemas.EmployeeCreate, db: Session):
    new_employee = models.Employee(**employee.dict())
    db.add(new_employee)
    db.flush()
    db.refresh(new_employee)
    return new_employee


def update_employee(employee: schemas.Employee, db: Session):
    updated_employee = models.Employee(**employee.dict())
    db.query(models.Employee).filter(models.Employee.id == updated_employee.id).update(
        jsonable_encoder(updated_employee)
    )
    db.commit()
    return (
        db.query(models.Employee)
        .filter(models.Employee.id == updated_employee.id)
        .first()
    )


def delete_employee(employee: schemas.Employee, db: Session):
    db.query(models.Employee).filter(models.Employee.id == employee.id).delete(
        synchronize_session="fetch"
    )
    db.commit()
    return
