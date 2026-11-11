from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.dependencies import usuario_actual
from app.errors import ErrorPanel
from app.services import gestion_usuarios as servicio
from app.services.gestion_usuarios import (
    AplicacionNoEncontrada, RolInexistente, UsuarioInvalido, UsuarioNoEncontrado,
)

router = APIRouter(prefix="/platform/applications/{client_id}/users", tags=["Usuarios"])


class UsuarioEntrada(BaseModel):
    nombre: str = Field(max_length=100)
    apellido: str = Field(max_length=100)
    roles: list[UUID]


def _como_error(e: Exception) -> ErrorPanel:
    if isinstance(e, AplicacionNoEncontrada):
        return ErrorPanel(404, str(e), motivo="aplicacion-inexistente")
    if isinstance(e, UsuarioNoEncontrado):
        return ErrorPanel(404, str(e), motivo="usuario-inexistente")
    if isinstance(e, RolInexistente):
        return ErrorPanel(404, str(e), motivo="rol-inexistente", rol_id=e.rol_id)
    if isinstance(e, UsuarioInvalido):
        return ErrorPanel(400, str(e), campo=e.campo)
    raise e


@router.get("/")
def listar(
    client_id: UUID,
    pagina: int = Query(1, ge=1),
    tamanio: int = Query(10, ge=1, le=100),
    admin: dict = Depends(usuario_actual),
):
    try:
        return servicio.listar_usuarios(client_id, admin["organizacion_id"], pagina, tamanio)
    except AplicacionNoEncontrada as e:
        raise _como_error(e)


@router.put("/{usuario_id}")
def editar(client_id: UUID, usuario_id: UUID, datos: UsuarioEntrada, admin: dict = Depends(usuario_actual)):
    try:
        return servicio.editar_usuario(
            client_id, usuario_id, admin["organizacion_id"], datos.nombre, datos.apellido, datos.roles
        )
    except (AplicacionNoEncontrada, UsuarioNoEncontrado, RolInexistente, UsuarioInvalido) as e:
        raise _como_error(e)


@router.delete("/{usuario_id}")
def eliminar(client_id: UUID, usuario_id: UUID, admin: dict = Depends(usuario_actual)):
    try:
        return servicio.eliminar_usuario(client_id, usuario_id, admin["organizacion_id"])
    except (AplicacionNoEncontrada, UsuarioNoEncontrado) as e:
        raise _como_error(e)
