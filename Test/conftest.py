import os

# Set env vars before any project imports that validate them at module load time.
# Tests use SQLite in memory and never touch MySQL.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key-not-for-production")

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from config.database import Base, get_db
from models.User import User as UserModel
from utils.jwt_manager import create_token

# Base de datos SQLite en memoria para tests — nunca toca MySQL
SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client():
    from main import app

    # Crear tablas en el SQLite de test
    Base.metadata.create_all(bind=engine_test)

    # Inyectar la DB de test en las rutas
    app.dependency_overrides[get_db] = override_get_db

    with (
        # jwt_bearer usa get_db() directo → apuntamos su SessionLocal al test
        patch("config.database.SessionLocal", TestingSessionLocal),
        # Evitar que el lifespan intente conectar a MySQL
        patch.object(Base.metadata, "create_all"),
        patch("main._seed_admin"),
    ):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="session")
def admin_headers(client):
    """Crea un usuario Administrador en la DB de test y devuelve sus headers JWT."""
    db = TestingSessionLocal()
    try:
        hashed = bcrypt.hashpw(b"Admin123", bcrypt.gensalt()).decode()
        user = UserModel(
            name="Admin Test",
            email="admin@test.com",
            password=hashed,
            rol="Administrador",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_token({"id": user.id, "email": user.email, "rol": user.rol})
    finally:
        db.close()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def empleado_headers(client):
    """Crea un usuario Empleado en la DB de test y devuelve sus headers JWT."""
    db = TestingSessionLocal()
    try:
        hashed = bcrypt.hashpw(b"Empleado123", bcrypt.gensalt()).decode()
        user = UserModel(
            name="Empleado Test",
            email="empleado@test.com",
            password=hashed,
            rol="Empleado",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_token({"id": user.id, "email": user.email, "rol": user.rol})
    finally:
        db.close()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def create_user():
    """
    Fixture factory: crea usuarios temporales en la DB de test.
    Los elimina automáticamente al terminar el test.
    """
    created_ids = []

    def _create(email: str, rol: str = "Empleado", name: str = "Temp User") -> int:
        db = TestingSessionLocal()
        try:
            hashed = bcrypt.hashpw(b"TempPass1", bcrypt.gensalt()).decode()
            user = UserModel(name=name, email=email, password=hashed, rol=rol)
            db.add(user)
            db.commit()
            db.refresh(user)
            created_ids.append(user.id)
            return user.id
        finally:
            db.close()

    yield _create

    # Cleanup: borra los usuarios creados durante el test
    db = TestingSessionLocal()
    try:
        for uid in created_ids:
            user = db.query(UserModel).filter(UserModel.id == uid).first()
            if user:
                db.delete(user)
        db.commit()
    finally:
        db.close()
