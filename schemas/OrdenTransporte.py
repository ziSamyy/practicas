import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class ValorEnviado(BaseModel):
    banco: str = Field(default="", max_length=100)
    numero: str = Field(default="", max_length=50)
    importe: Optional[Decimal] = None


class OrdenTransporteBase(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore",
    )

    cliente_id: PositiveInt
    descripcion: str = Field(min_length=1, max_length=500)
    contacto: Optional[str] = Field(default=None, max_length=100)
    movil: Optional[str] = Field(default=None, max_length=20)
    valores_enviados: Optional[List[ValorEnviado]] = None
    valor_declarado: Optional[Decimal] = None
    efectivo_enviado: Optional[Decimal] = None
    flete_a_cargo_de: Optional[str] = Field(default=None, max_length=50)
    transporte: Optional[str] = Field(default=None, max_length=100)
    emitio_la_orden: str = Field(min_length=2, max_length=100)
    fecha_envio: datetime.date


class OrdenTransporteCreate(OrdenTransporteBase):
    pass


class OrdenTransporteUpdate(OrdenTransporteBase):
    pass


class OrdenTransporteResponse(OrdenTransporteBase):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore",
        from_attributes=True,
    )

    id: PositiveInt
