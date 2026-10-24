import hashlib
import secrets

from app.database import obtener_conexion


class NombreAppDuplicado(Exception):
    pass


def _conectar():
    conexion = obtener_conexion()
    if conexion is None:
        raise RuntimeError("No se pudo conectar a la base de datos")
    return conexion


def _hash_secret(client_secret: str) -> str:
    # el secret es aleatorio y largo, así que alcanza con SHA-256 (es el formato que usa la base)
    return hashlib.sha256(client_secret.encode()).hexdigest()


def crear_aplicacion(nombre: str, descripcion: str, organizacion_id) -> dict:
    nombre = nombre.strip()
    descripcion = (descripcion or "").strip()
    client_secret = secrets.token_urlsafe(32)

    with _conectar() as conn:
        existe = conn.execute(
            "SELECT 1 FROM aplicacion WHERE organizacion_id = %s AND lower(nombre) = lower(%s)",
            (organizacion_id, nombre),
        ).fetchone()
        if existe:
            raise NombreAppDuplicado(f"Ya existe una aplicación con el nombre '{nombre}'")
        fila = conn.execute(
            """
            INSERT INTO aplicacion (organizacion_id, nombre, descripcion, hash_secret)
            VALUES (%s, %s, %s, %s)
            RETURNING client_id
            """,
            (organizacion_id, nombre, descripcion, _hash_secret(client_secret)),
        ).fetchone()

    return {"nombre": nombre, "client_id": str(fila[0]), "client_secret": client_secret}


def listar_aplicaciones(organizacion_id) -> list:
    with _conectar() as conn:
        filas = conn.execute(
            """
            SELECT client_id, nombre, descripcion, creado_en
            FROM aplicacion
            WHERE organizacion_id = %s
            ORDER BY creado_en DESC
            """,
            (organizacion_id,),
        ).fetchall()

    return [
        {"client_id": str(f[0]), "nombre": f[1], "descripcion": f[2], "creado_en": f[3].isoformat()}
        for f in filas
    ]


def regenerar_secret(client_id, organizacion_id) -> dict:
    client_secret = secrets.token_urlsafe(32)

    with _conectar() as conn:
        fila = conn.execute(
            """
            UPDATE aplicacion
            SET hash_secret = %s
            WHERE client_id = %s AND organizacion_id = %s
            RETURNING client_id
            """,
            (_hash_secret(client_secret), client_id, organizacion_id),
        ).fetchone()

    if fila is None:
        raise ValueError("Aplicación no encontrada")

    return {"client_id": str(fila[0]), "client_secret": client_secret}
