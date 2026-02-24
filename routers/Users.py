from typing import List

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.database import get_db
from middlewares.jwt_bearer import JWTBearer
from models.User import User as UserModel
from schemas.User import UserCreate, UserLogin, UserResponse
from utils.jwt_manager import create_token


user_route = APIRouter()


def require_admin(token_data: dict = Depends(JWTBearer())) -> dict:
    if token_data.get("rol") != "Administrador":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden realizar esta acción")
    return token_data


@user_route.post("/login", tags=["Auth"])
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not bcrypt.checkpw(
        user.password.get_secret_value().encode("utf-8"),
        db_user.password.encode("utf-8"),
    ):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    token_data = {"id": db_user.id, "email": db_user.email, "rol": db_user.rol}
    token = create_token(token_data)
    return {
        "token": token,
        "user": UserResponse.model_validate(db_user),
    }


@user_route.post("/usuarios", tags=["Usuarios"], response_model=UserResponse)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    existing_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    hashed_password = bcrypt.hashpw(
        user.password.get_secret_value().encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    new_user = UserModel(
        name=user.name, email=user.email, password=hashed_password, rol=user.rol
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse.model_validate(new_user)


@user_route.get(
    "/usuarios",
    tags=["Usuarios"],
    response_model=List[UserResponse],
    dependencies=[Depends(require_admin)],
)
def get_usuarios(db: Session = Depends(get_db)):
    return db.query(UserModel).all()


@user_route.get(
    "/usuarios/{usuario_id}",
    tags=["Usuarios"],
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
def get_usuario_por_id(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(UserModel).filter(UserModel.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@user_route.put(
    "/usuarios/{usuario_id}",
    tags=["Usuarios"],
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
def update_usuario(
    usuario_id: int, user_update: UserCreate, db: Session = Depends(get_db)
):
    usuario = db.query(UserModel).filter(UserModel.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    hashed_password = bcrypt.hashpw(
        user_update.password.get_secret_value().encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    usuario.name = user_update.name
    usuario.email = user_update.email
    usuario.password = hashed_password
    usuario.rol = user_update.rol

    db.commit()
    db.refresh(usuario)

    return usuario


@user_route.delete(
    "/usuarios/{usuario_id}",
    tags=["Usuarios"],
    dependencies=[Depends(require_admin)],
)
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(UserModel).filter(UserModel.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(usuario)
    db.commit()

    return {"msg": "Usuario eliminado correctamente"}
