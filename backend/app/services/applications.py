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

def listar_aplicaciones(org_id: int) -> list:
    with _conectar() as conn:
        filas = conn.execute(
            """
            SELECT id, name, description, client_id, created_at
            FROM applications
            WHERE org_id = %s
            ORDER BY created_at DESC
            """,
            (org_id,),
        ).fetchall()

    return [
        {
            "id": f[0],
            "name": f[1],
            "description": f[2],
            "client_id": f[3],
            "created_at": str(f[4]),
        }
        for f in filas
    ]

def regenerar_secret(app_id: int) -> dict:
    client_secret = str(uuid.uuid4())
    secret_hash = bcrypt.hashpw(client_secret.encode(), bcrypt.gensalt()).decode()

    try:
            with _conectar() as conn:
                fila = conn.execute(
                    """
                    UPDATE applications
                    SET client_secret_hash = %s
                    WHERE id = %s
                    RETURNING id, client_id
                    """,
                    (secret_hash, app_id),
                ).fetchone()
    except Exception as e:
        raise RuntimeError(f"Error al regenerar secret: {e}")

    if fila is None:
        raise ValueError("Aplicación no encontrada")

    return {
        "id": fila[0],
        "client_id": fila[1],
        "client_secret": client_secret,
    }
