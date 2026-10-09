import bcrypt
import psycopg

from app.database import obtener_conexion
from app.utils.validators import normalizar_email, validar_password

ROL_USUARIO = "usuario"  # rol que se asigna por defecto al registrarse


class EmailYaRegistrado(Exception):
    pass


def _conectar():
    # obtener_conexion() devuelve None si falla; acá lo convertimos en un error claro
    conexion = obtener_conexion()
    if conexion is None:
        raise RuntimeError("No se pudo conectar a la base de datos")
    return conexion


def buscar_por_email(email: str):
    """Devuelve (id, username, email, password_hash) o None si no existe."""
    with _conectar() as conn:
        return conn.execute(
            "SELECT id, username, email, password_hash FROM users WHERE email = %s",
            (normalizar_email(email),),
        ).fetchone()


def registrar_usuario(username: str, email: str, password: str) -> dict:
    email = normalizar_email(email)
    validar_password(password)  # lanza ValueError si incumple alguna regla

    # bcrypt trabaja con bytes; gensalt() genera un salt aleatorio por usuario
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        # el "with" hace commit al salir bien y rollback si hay error
        with _conectar() as conn:
            fila = conn.execute(
                """
                INSERT INTO users (username, email, password_hash, id_rol)
                VALUES (%s, %s, %s, (SELECT id FROM roles WHERE nombre = %s))
                RETURNING id, username, email
                """,
                (username, email, password_hash, ROL_USUARIO),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        # la columna email es UNIQUE: la base rechaza duplicados
        raise EmailYaRegistrado(f"El email {email} ya está registrado")

    # se devuelve sin el hash para no exponerlo
    return {"id": fila[0], "username": fila[1], "email": fila[2]}


class CredencialesInvalidas(Exception):
    pass


def autenticar_usuario(email: str, password: str) -> dict:
    fila = buscar_por_email(email)

    # mismo error si no existe el email o si la contraseña está mal,
    # así no se revela qué emails están registrados
    if fila is None or not bcrypt.checkpw(password.encode(), fila[3].encode()):
        raise CredencialesInvalidas("Email o contraseña incorrectos")

    return {"id": fila[0], "username": fila[1], "email": fila[2]}


def buscar_por_id(id_usuario: int):
    """Devuelve {id, username, email} o None si no existe."""
    with _conectar() as conn:
        fila = conn.execute(
            "SELECT id, username, email FROM users WHERE id = %s", (id_usuario,)
        ).fetchone()
    return None if fila is None else {"id": fila[0], "username": fila[1], "email": fila[2]}
