"""Formato único de error para las rutas del panel.

Todas responden {"detail": "...", "campo": "...", "reinicio": false}, más claves extra opcionales
(por ejemplo "motivo" o "cantidad_usuarios"). Es el mismo formato que ya usa /register.
Las rutas de la API externa (/auth/...) conservan su formato original.
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorPanel(HTTPException):
    def __init__(self, status_code: int, detail: str, campo: str = "general", reinicio: bool = False, **extra):
        super().__init__(status_code=status_code, detail=detail)
        self.campo = campo
        self.reinicio = reinicio
        self.extra = extra


async def manejar_error_http(request: Request, e: StarletteHTTPException):
    if request.url.path.startswith("/auth/"):
        cuerpo = {"detail": e.detail}
    else:
        cuerpo = {
            "detail": e.detail,
            "campo": getattr(e, "campo", "general"),
            "reinicio": getattr(e, "reinicio", False),
            **getattr(e, "extra", {}),
        }
    return JSONResponse(status_code=e.status_code, content=cuerpo, headers=getattr(e, "headers", None))
