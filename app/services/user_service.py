from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app import schemas, models
from app.dependencies import get_password_hash


def get_user(username: str, db: Session):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(user: schemas.User, db: Session):
    new_user = models.User(**user.dict())
    new_user.hashed_pwd = get_password_hash(user.hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
