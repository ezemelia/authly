from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import usuario_actual
from app.services.applications import crear_aplicacion, NombreAppDuplicado, regenerar_secret, listar_aplicaciones, editar_aplicacion, eliminar_aplicacion
router = APIRouter(prefix="/platform/applications", tags=["Aplicaciones"])


class AplicacionEntrada(BaseModel):
    nombre: str
    descripcion: str = ""


@router.post("/", status_code=201)
def crear_app(datos: AplicacionEntrada, admin: dict = Depends(usuario_actual)):
    if not datos.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    try:
        return crear_aplicacion(datos.nombre, datos.descripcion, admin["organizacion_id"])
    except NombreAppDuplicado as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/")
def listar_apps(admin: dict = Depends(usuario_actual)):
    return listar_aplicaciones(admin["organizacion_id"])


@router.post("/{client_id}/regenerar-secret")
def regenerar(client_id: UUID, admin: dict = Depends(usuario_actual)):
    try:
        return regenerar_secret(client_id, admin["organizacion_id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{client_id}")
def editar_app(client_id: UUID, datos: AplicacionEntrada, admin: dict = Depends(usuario_actual)):
    if not datos.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    try:
        return editar_aplicacion(client_id, datos.nombre, datos.descripcion, admin["organizacion_id"])
    except NombreAppDuplicado as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{client_id}", status_code=204)
def eliminar_app(client_id: UUID, admin: dict = Depends(usuario_actual)):
    try:
        eliminar_aplicacion(client_id, admin["organizacion_id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))