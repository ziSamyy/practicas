from fastapi.security import HTTPBearer
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session

from config.database import get_db
from models.User import User as UserModel
from utils.jwt_manager import validate_token


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        auth = await super().__call__(request)

        try:
            data = validate_token(auth.credentials)
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid or malformed token.")

        db: Session = next(get_db())
        try:
            db_user = db.query(UserModel).filter(UserModel.email == data.get("email")).first()
        finally:
            db.close()

        if not db_user:
            raise HTTPException(status_code=403, detail="Unauthorized.")

        return data
