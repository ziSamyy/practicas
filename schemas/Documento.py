from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from schemas.Client import ClientResponse
from schemas.User import UserResponse


# ── Items ──────────────────────────────────────────────────────────────────

class DocumentoItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    descripcion:     str     = Field(min_length=1, max_length=500)
    cantidad:        Decimal = Field(gt=0, decimal_places=2)
    precio_unitario: Decimal = Field(gt=0, decimal_places=2)


class DocumentoItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              PositiveInt
    descripcion:     str
    cantidad:        Decimal
    precio_unitario: Decimal
    subtotal:        Decimal


# ── Documento ───────────────────────────────────────────────────────────────

class DocumentoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    cliente_id:         PositiveInt
    empresa_transporte: str = Field(min_length=2, max_length=200)
    a_cargo_de:         str = Field(min_length=2, max_length=200)
    items:              List[DocumentoItemCreate] = Field(min_length=1)


class DocumentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                 PositiveInt
    numero:             str
    fecha_emision:      datetime
    empresa_transporte: str
    a_cargo_de:         str
    total:              Decimal
    cliente:            ClientResponse
    usuario:            UserResponse
    items:              List[DocumentoItemResponse]
