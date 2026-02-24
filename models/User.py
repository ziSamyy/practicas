from config.database import Base
from sqlalchemy import Column, Integer, String, Enum


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    rol = Column(Enum("Administrador", "Empleado", name="rol_user"), nullable=False)
