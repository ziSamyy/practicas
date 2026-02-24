from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.database import get_db
from middlewares.jwt_bearer import JWTBearer
from models.Client import Client as ClientModel
from schemas.Client import ClientCreate, ClientUpdate, ClientResponse

client_route = APIRouter()


@client_route.post(
    "/clientes",
    tags=["Clientes"],
    response_model=ClientResponse,
    dependencies=[Depends(JWTBearer())],
)
def crear_cliente(client: ClientCreate, db: Session = Depends(get_db)):
    if db.query(ClientModel).filter(ClientModel.cuit == client.cuit).first():
        raise HTTPException(status_code=400, detail="El CUIT ya está registrado")

    if db.query(ClientModel).filter(ClientModel.email == client.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    new_client = ClientModel(**client.model_dump())
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client


@client_route.get(
    "/clientes",
    tags=["Clientes"],
    response_model=List[ClientResponse],
    dependencies=[Depends(JWTBearer())],
)
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(ClientModel).all()


@client_route.get(
    "/clientes/{cliente_id}",
    tags=["Clientes"],
    response_model=ClientResponse,
    dependencies=[Depends(JWTBearer())],
)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    client = db.query(ClientModel).filter(ClientModel.id == cliente_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@client_route.put(
    "/clientes/{cliente_id}",
    tags=["Clientes"],
    response_model=ClientResponse,
    dependencies=[Depends(JWTBearer())],
)
def actualizar_cliente(
    cliente_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)
):
    client = db.query(ClientModel).filter(ClientModel.id == cliente_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Verificar duplicados solo si el valor cambió
    if client_update.cuit != client.cuit:
        if db.query(ClientModel).filter(ClientModel.cuit == client_update.cuit).first():
            raise HTTPException(status_code=400, detail="El CUIT ya está registrado")

    if client_update.email != client.email:
        if db.query(ClientModel).filter(ClientModel.email == client_update.email).first():
            raise HTTPException(status_code=400, detail="El email ya está registrado")

    for field, value in client_update.model_dump().items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


@client_route.delete(
    "/clientes/{cliente_id}",
    tags=["Clientes"],
    dependencies=[Depends(JWTBearer())],
)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    client = db.query(ClientModel).filter(ClientModel.id == cliente_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    db.delete(client)
    db.commit()
    return {"msg": "Cliente eliminado correctamente"}
