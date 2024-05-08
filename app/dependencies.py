from app.database import SessionLocal
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def verify_password(plain_password, hashed_password):
    print("[-] Verifying...")
    result = pwd_context.verify(plain_password, hashed_password)
    if result:
        print("[!] Verification succeed!")
    return result


def get_password_hash(password):
    return pwd_context.hash(password)
