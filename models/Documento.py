from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from config.database import Base


class Documento(Base):
    __tablename__ = "documentos"

    id                 = Column(Integer, primary_key=True, index=True)
    numero             = Column(String(20), unique=True, nullable=False, index=True)
    fecha_emision      = Column(DateTime, nullable=False,
                                default=lambda: datetime.now(timezone.utc))
    cliente_id         = Column(Integer, ForeignKey("clients.id"), nullable=False)
    usuario_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    empresa_transporte = Column(String(200), nullable=False)
    a_cargo_de         = Column(String(200), nullable=False)
    total              = Column(Numeric(12, 2), nullable=False)

    cliente = relationship("Client", lazy="joined")
    usuario = relationship("User", lazy="joined")
    items   = relationship(
        "DocumentoItem",
        back_populates="documento",
        cascade="all, delete-orphan",
        lazy="joined",
    )


class DocumentoItem(Base):
    __tablename__ = "documento_items"

    id              = Column(Integer, primary_key=True, index=True)
    documento_id    = Column(Integer, ForeignKey("documentos.id"), nullable=False)
    descripcion     = Column(String(500), nullable=False)
    cantidad        = Column(Numeric(10, 2), nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    subtotal        = Column(Numeric(12, 2), nullable=False)

    documento = relationship("Documento", back_populates="items")
