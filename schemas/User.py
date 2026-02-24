from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PositiveInt, SecretStr, field_validator


class UserBase(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )
    name: str = Field(min_length=3, max_length=50)
    email: EmailStr = Field(max_length=100)
    rol: Literal["Administrador", "Empleado"] = "Empleado"


class UserCreate(UserBase):
    password: SecretStr = Field(min_length=8, max_length=255)

    @field_validator("password")
    @classmethod
    def validar_password(cls, password_secret: SecretStr) -> SecretStr:
        p = password_secret.get_secret_value()

        if not (any(c.isdigit() for c in p) and
                any(c.islower() for c in p) and
                any(c.isupper() for c in p)):
            raise ValueError(
                "La contraseña debe contener al menos: "
                "un número, una letra minúscula y una letra mayúscula."
            )

        return password_secret


class UserResponse(UserBase):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
        from_attributes=True,
    )

    id: PositiveInt


class UserLogin(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='ignore',
    )

    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=255)
