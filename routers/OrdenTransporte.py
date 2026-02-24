from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from config.database import get_db
from middlewares.jwt_bearer import JWTBearer
from models.Client import Client as ClientModel
from models.OrdenTransporte import OrdenTransporte as OrdenModel
from schemas.OrdenTransporte import (
    OrdenTransporteCreate,
    OrdenTransporteResponse,
    OrdenTransporteUpdate,
)
from utils.pdf_orden_transporte import generar_pdf_orden_transporte

orden_route = APIRouter()


def _get_orden_or_404(orden_id: int, db: Session) -> OrdenModel:
    orden = db.query(OrdenModel).filter(OrdenModel.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de transporte no encontrada")
    return orden


def _get_cliente_or_404(cliente_id: int, db: Session) -> ClientModel:
    client = db.query(ClientModel).filter(ClientModel.id == cliente_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@orden_route.post(
    "/ordenes",
    tags=["Ordenes de Transporte"],
    response_model=OrdenTransporteResponse,
    dependencies=[Depends(JWTBearer())],
)
def crear_orden(orden: OrdenTransporteCreate, db: Session = Depends(get_db)):
    _get_cliente_or_404(orden.cliente_id, db)

    data = orden.model_dump()
    # Serializar valores_enviados a lista de dicts planos para JSON
    if data.get("valores_enviados"):
        data["valores_enviados"] = [
            {k: (str(v) if v is not None else None) for k, v in val.items()}
            for val in data["valores_enviados"]
        ]

    new_orden = OrdenModel(**data)
    db.add(new_orden)
    db.commit()
    db.refresh(new_orden)
    return new_orden


@orden_route.get(
    "/ordenes",
    tags=["Ordenes de Transporte"],
    response_model=List[OrdenTransporteResponse],
    dependencies=[Depends(JWTBearer())],
)
def listar_ordenes(db: Session = Depends(get_db)):
    return db.query(OrdenModel).all()


@orden_route.get(
    "/ordenes/{orden_id}",
    tags=["Ordenes de Transporte"],
    response_model=OrdenTransporteResponse,
    dependencies=[Depends(JWTBearer())],
)
def obtener_orden(orden_id: int, db: Session = Depends(get_db)):
    return _get_orden_or_404(orden_id, db)


@orden_route.put(
    "/ordenes/{orden_id}",
    tags=["Ordenes de Transporte"],
    response_model=OrdenTransporteResponse,
    dependencies=[Depends(JWTBearer())],
)
def actualizar_orden(
    orden_id: int, orden_update: OrdenTransporteUpdate, db: Session = Depends(get_db)
):
    orden = _get_orden_or_404(orden_id, db)
    _get_cliente_or_404(orden_update.cliente_id, db)

    data = orden_update.model_dump()
    if data.get("valores_enviados"):
        data["valores_enviados"] = [
            {k: (str(v) if v is not None else None) for k, v in val.items()}
            for val in data["valores_enviados"]
        ]

    for field, value in data.items():
        setattr(orden, field, value)

    db.commit()
    db.refresh(orden)
    return orden


@orden_route.delete(
    "/ordenes/{orden_id}",
    tags=["Ordenes de Transporte"],
    dependencies=[Depends(JWTBearer())],
)
def eliminar_orden(orden_id: int, db: Session = Depends(get_db)):
    orden = _get_orden_or_404(orden_id, db)
    db.delete(orden)
    db.commit()
    return {"msg": "Orden eliminada correctamente"}


@orden_route.get(
    "/ordenes/{orden_id}/pdf",
    tags=["Ordenes de Transporte"],
    dependencies=[Depends(JWTBearer())],
    response_class=Response,
)
def descargar_pdf(orden_id: int, db: Session = Depends(get_db)):
    orden = _get_orden_or_404(orden_id, db)
    cliente = _get_cliente_or_404(orden.cliente_id, db)

    orden_dict = {
        "descripcion":       orden.descripcion,
        "contacto":          orden.contacto,
        "movil":             orden.movil,
        "valores_enviados":  orden.valores_enviados,
        "valor_declarado":   orden.valor_declarado,
        "efectivo_enviado":  orden.efectivo_enviado,
        "flete_a_cargo_de":  orden.flete_a_cargo_de,
        "transporte":        orden.transporte,
        "emitio_la_orden":   orden.emitio_la_orden,
        "fecha_envio":       orden.fecha_envio,
    }

    cliente_dict = {
        "name":      cliente.name,
        "cuit":      cliente.cuit,
        "telefono":  cliente.telefono,
        "domicilio": cliente.domicilio,
        "ciudad":    cliente.ciudad,
        "provincia": cliente.provincia,
    }

    pdf_bytes = generar_pdf_orden_transporte(orden_dict, cliente_dict)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="orden_{orden_id}.pdf"'
        },
    )
