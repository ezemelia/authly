from fastapi import APIRouter, HTTPException
from app.services.applications import crear_aplicacion, NombreAppDuplicado, regenerar_secret, listar_aplicaciones

router = APIRouter(prefix="/api/platform/applications", tags=["Aplicaciones"])


@router.post("/", status_code=201)
def crear_app(nombre: str, descripcion: str = None, org_id: int = 1):
    try:
        return crear_aplicacion(nombre, descripcion, org_id)
    except NombreAppDuplicado as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/")
def listar_apps(org_id: int = 1):
    return listar_aplicaciones(org_id)

@router.post("/{app_id}/regenerar-secret")
def regenerar(app_id: int):
    try:
        return regenerar_secret(app_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))