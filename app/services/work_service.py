from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app import schemas, models
from app.models import Work, WorkSpecification

from datetime import datetime


def get_work(work_id: int, db: Session):
    return db.query(Work).filter(Work.id == work_id).first()


def get_works(db: Session):
    return db.query(Work).all()


def get_works_by_batch_process_id(batch_process_id: int, db: Session):
    return db.query(Work).filter(Work.batch_process_id == batch_process_id).all()


def get_works_by_employee_id(employee_id: int, db: Session):
    return db.query(Work).filter(Work.employee_id == employee_id).all()


def get_works_in_work_date_range(after: datetime, before: datetime, db: Session):
    return (
        db.query(Work).filter(Work.work_date >= after, Work.work_date <= before).all()
    )


def get_works_by_employee_id_and_work_date_range(
    employee_id: int, after: datetime, before: datetime, db: Session
):
    return (
        db.query(Work)
        .filter(
            Work.employee_id == employee_id,
            Work.work_date >= after,
            Work.work_date <= before,
        )
        .all()
    )


def get_unchecked_works_by_employee_id_and_work_date_range(
    employee_id: int, after: datetime, before: datetime, db: Session
):
    return (
        db.query(Work)
        .filter(
            Work.employee_id == employee_id,
            Work.work_date >= after,
            Work.work_date <= before,
            Work.check == False,
        )
        .all()
    )


def get_works_by_check_status(check: bool, db: Session):
    return db.query(Work).filter(Work.check == check).all()


def create_work(work: schemas.WorkCreate, db: Session):
    new_work = Work(**work.dict())
    db.add(new_work)
    db.flush()
    db.refresh(new_work)
    return new_work


def update_work(work: schemas.Work, db: Session):
    json_work = jsonable_encoder(work)
    json_work_specifications = json_work.pop("work_specification")
    db_work = Work(**json_work)
    db.query(Work).filter(Work.id == db_work.id).update(json_work)
    if json_work_specifications:
        for ws in json_work_specifications:
            db_ws = WorkSpecification(**ws)
            db.query(WorkSpecification).filter(WorkSpecification.id == db_ws.id).update(
                ws
            )
    db.commit()
    return db.query(Work).filter(Work.id == db_work.id).first()


def delete_work(work: schemas.Work, db: Session):
    db.query(Work).filter(Work.id == work.id).delete(synchronize_session="fetch")
    db.commit()
    return
