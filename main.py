import secrets
import string
from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.database import engine, Base, SessionLocal
from middlewares.error_handler import ErrorHandler
from models.User import User as UserModel
import models.Documento        # registra Documento y DocumentoItem en Base.metadata
import models.OrdenTransporte  # registra OrdenTransporte en Base.metadata
from routers.Users import user_route
from routers.Client import client_route
from routers.Documento import documento_route
from routers.OrdenTransporte import orden_route


def _generate_password(length: int = 16) -> str:
    """Genera una contraseña aleatoria segura que cumple los requisitos de validación."""
    chars = string.ascii_letters + string.digits
    while True:
        pwd = "".join(secrets.choice(chars) for _ in range(length))
        if (any(c.islower() for c in pwd) and
                any(c.isupper() for c in pwd) and
                any(c.isdigit() for c in pwd)):
            return pwd


def _seed_admin() -> None:
    """Crea el usuario administrador por defecto si no existe."""
    db = SessionLocal()
    try:
        existing = db.query(UserModel).filter(UserModel.email == "admin@admin.com").first()
        if existing:
            return

        password = _generate_password()
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        admin = UserModel(
            name="Admin",
            email="admin@admin.com",
            password=hashed,
            rol="Administrador",
        )
        db.add(admin)
        db.commit()

        print("\n" + "=" * 52)
        print("  USUARIO ADMINISTRADOR CREADO POR PRIMERA VEZ")
        print("=" * 52)
        print(f"  Email:      admin@admin.com")
        print(f"  Contraseña: {password}")
        print("=" * 52)
        print("  Guarda esta contraseña. No se mostrará de nuevo.")
        print("=" * 52 + "\n")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed_admin()
    yield


app = FastAPI(
    title="Mi aplicación con FastAPI",
    version="0.0.1",
    lifespan=lifespan,
)

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5501",
    "http://127.0.0.1:5502",
    "http://localhost:5502",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(ErrorHandler)

app.include_router(user_route)
app.include_router(client_route)
app.include_router(documento_route)
app.include_router(orden_route)
