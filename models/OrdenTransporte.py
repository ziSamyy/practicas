from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship

from config.database import Base


class OrdenTransporte(Base):
    __tablename__ = "ordenes_transporte"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    descripcion = Column(String(500), nullable=False)
    contacto = Column(String(100), nullable=True)
    movil = Column(String(20), nullable=True)

    # JSON list of {banco, numero, importe}
    valores_enviados = Column(JSON, nullable=True)

    valor_declarado = Column(Numeric(12, 2), nullable=True)
    efectivo_enviado = Column(Numeric(12, 2), nullable=True)

    flete_a_cargo_de = Column(String(50), nullable=True)
    transporte = Column(String(100), nullable=True)
    emitio_la_orden = Column(String(100), nullable=False)
    fecha_envio = Column(Date, nullable=False)

    cliente = relationship("Client", backref="ordenes_transporte")
