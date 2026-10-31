import hashlib
from fastapi import Depends, HTTPException, Header
from app.database import obtener_conexion


def _hash_secreto(secreto: str) -> str:
    """SHA-256 del client_secret para comparar contra el hash almacenado."""
    return hashlib.sha256(secreto.encode()).hexdigest()


def aplicacion_actual(
    x_client_id: str = Header(...),
    x_client_secret: str = Header(...),
):
    """Dependency que valida las credenciales de una aplicación externa.
    Usada por los endpoints de la API pública (CU-05, 07, 09, 11).
    """
    conn = obtener_conexion()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT client_id, nombre, organizacion_id, hash_secret "
                "FROM authly.aplicacion WHERE client_id = %s",
                (x_client_id,),
            )
            fila = cur.fetchone()
    finally:
        conn.close()

    if fila is None:
        raise HTTPException(status_code=401, detail="Credenciales de aplicación inválidas")

    client_id, nombre, org_id, hash_secret = fila

    if _hash_secreto(x_client_secret) != hash_secret:
        raise HTTPException(status_code=401, detail="Credenciales de aplicación inválidas")

    return {
        "id": client_id,
        "nombre": nombre,
        "organizacion_id": str(org_id),
    }
