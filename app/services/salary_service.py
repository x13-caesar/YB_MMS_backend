from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder

from app import schemas, models

from datetime import datetime


def get_salary(salary_id: int, db: Session):
    return db.query(models.Salary).filter(models.Salary.id == salary_id).first()


def get_salaries(db: Session):
    return db.query(models.Salary).all()


def get_salaries_by_status(status: str, db: Session):
    return db.query(models.Salary).filter(models.Salary.status == status).all()


def get_salaries_by_employee_id(employee_id: int, db: Session):
    return (
        db.query(models.Salary).filter(models.Salary.employee_id == employee_id).all()
    )


def get_salaries_in_month_range(after: datetime, before: datetime, db: Session):
    return (
        db.query(models.Employee)
        .filter(models.Salary.start_date >= after, models.Salary.end_date <= before)
        .all()
    )


def create_salary(salary: schemas.SalaryCreate, db: Session):
    new_salary = models.Salary(**salary.dict())
    db.add(new_salary)
    db.commit()
    db.refresh(new_salary)
    return new_salary


def update_salary(salary: schemas.Salary, db: Session):
    json_salary = jsonable_encoder(salary)
    # json_works = json_salary.pop("work", None)
    # json_day_invoice = json_salary.pop("day_invoice", None)
    db_salary = models.Salary(**json_salary)
    db.query(models.Salary).filter(models.Salary.id == db_salary.id).update(
        jsonable_encoder(db_salary)
    )
    # if json_works:
    #     for w in json_works:
    #         db_work = schemas.Work(**w)
    #         work_service.update_work(db_work, db=db)
    # if json_day_invoice:
    #     for di in json_day_invoice:
    #         db_di = schemas.DayInvoice(**di)
    #         day_invoice_service.update_day_invoice(db_di, db=db)
    db.commit()
    return db.query(models.Salary).filter(models.Salary.id == db_salary.id).first()


def delete_salary(salary: schemas.Salary, db: Session):
    db.query(models.Salary).filter(models.Salary.id == salary.id).delete(
        synchronize_session="fetch"
    )
    db.commit()
    return
