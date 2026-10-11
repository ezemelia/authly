import uuid
import bcrypt
import psycopg

from app.database import obtener_conexion


class NombreAppDuplicado(Exception):
    pass


def _conectar():
    conexion = obtener_conexion()
    if conexion is None:
        raise RuntimeError("No se pudo conectar a la base de datos")
    return conexion


def crear_aplicacion(nombre: str, descripcion: str, org_id: int) -> dict:
    client_id = str(uuid.uuid4())
    client_secret = str(uuid.uuid4())
    secret_hash = bcrypt.hashpw(client_secret.encode(), bcrypt.gensalt()).decode()

    try:
        with _conectar() as conn:
            fila = conn.execute(
                """
                INSERT INTO applications (org_id, name, description, client_id, client_secret_hash)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (org_id, nombre, descripcion, client_id, secret_hash),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise NombreAppDuplicado(f"Ya existe una aplicación con el nombre '{nombre}'")

    return {
        "id": fila[0],
        "nombre": nombre,
        "client_id": client_id,
        "client_secret": client_secret,
    }