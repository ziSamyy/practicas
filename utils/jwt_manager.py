import os

from dotenv import load_dotenv
from jwt import encode, decode

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is not set")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 30


def create_token(data: dict) -> str:
    from datetime import datetime, timedelta, timezone
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)


def validate_token(token: str) -> dict:
    return decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
