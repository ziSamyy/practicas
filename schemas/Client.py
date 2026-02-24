import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PositiveInt, field_validator


class ClientBase(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )

    cuit: str = Field(min_length=13, max_length=13)
    name: str = Field(min_length=3, max_length=100)
    email: EmailStr = Field(max_length=100)
    telefono: str = Field(min_length=7, max_length=20)
    domicilio: str = Field(min_length=5, max_length=255)
    ciudad: str = Field(min_length=2, max_length=100)
    provincia: str = Field(min_length=2, max_length=100)

    @field_validator("cuit")
    @classmethod
    def validar_cuit(cls, v: str) -> str:
        if not re.fullmatch(r"\d{2}-\d{8}-\d", v):
            raise ValueError("El CUIT debe tener el formato XX-XXXXXXXX-X")
        return v


class ClientCreate(ClientBase):
    """Esquema para crear un nuevo cliente."""
    pass


class ClientUpdate(ClientBase):
    """Esquema para actualizar un cliente existente."""
    pass


class ClientResponse(ClientBase):
    """Esquema para retornar datos del cliente."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
        from_attributes=True,
    )

    id: PositiveInt
