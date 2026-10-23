from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.database import obtener_conexion
from app.utils.validators import normalizar_email

_hasher = PasswordHasher()  # los hashes de la base (administrador.hash_contrasena) son argon2

def _conectar():
    # obtener_conexion() devuelve None si falla; acá lo convertimos en un error claro
    conexion = obtener_conexion()
    if conexion is None:
        raise RuntimeError("No se pudo conectar a la base de datos")
    return conexion


def buscar_por_email(email: str):
    """Devuelve (id, nombre, apellido, email, hash_contrasena, organizacion_id) del administrador, o None."""
    with _conectar() as conn:
        return conn.execute(
            """
            SELECT id, nombre, apellido, email, hash_contrasena, organizacion_id
            FROM administrador WHERE email = %s
            """,
            (normalizar_email(email),),
        ).fetchone()


class CredencialesInvalidas(Exception):
    pass


def _password_correcta(password: str, hash_guardado: str) -> bool:
    try:
        return _hasher.verify(hash_guardado, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def autenticar_usuario(email: str, password: str) -> dict:
    fila = buscar_por_email(email)

    # mismo error si no existe el email o si la contraseña está mal,
    # así no se revela qué emails están registrados
    if fila is None or not _password_correcta(password, fila[4]):
        raise CredencialesInvalidas("Email o contraseña incorrectos")

    return {"id": fila[0], "nombre": fila[1], "apellido": fila[2], "email": fila[3], "organizacion_id": fila[5]}


def buscar_por_id(id_usuario: str):
    """Devuelve los datos del administrador o None si no existe."""
    with _conectar() as conn:
        fila = conn.execute(
            "SELECT id, nombre, apellido, email, organizacion_id FROM administrador WHERE id = %s",
            (id_usuario,),
        ).fetchone()
    if fila is None:
        return None
    return {"id": fila[0], "nombre": fila[1], "apellido": fila[2], "email": fila[3], "organizacion_id": fila[4]}
