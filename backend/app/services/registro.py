import hashlib
import re
import secrets

import psycopg
from argon2 import PasswordHasher

from app.database import obtener_conexion
from app.utils.validators import normalizar_email, validar_password

_hasher = PasswordHasher()

MINUTOS_VALIDEZ_CODIGO = 10
MAX_INTENTOS = 5


class RegistroInvalido(Exception):
    """Dato inválido o ya en uso. `campo` indica qué campo del formulario marcar."""

    def __init__(self, mensaje: str, campo: str = "general", reinicio: bool = False):
        super().__init__(mensaje)
        self.campo = campo
        self.reinicio = reinicio  # True: el frontend debe volver a empezar el registro


def _conectar():
    conexion = obtener_conexion()
    if conexion is None:
        raise RuntimeError("No se pudo conectar a la base de datos")
    return conexion


def _hash_codigo(email: str, codigo: str) -> str:
    return hashlib.sha256(f"{email}:{codigo}".encode()).hexdigest()


def _validar_datos(nombre, apellido, email, password, organizacion, cuit):
    for valor, campo in ((nombre, "nombre"), (apellido, "apellido"), (organizacion, "organizacion")):
        if not valor.strip():
            raise RegistroInvalido("Campo incompleto.", campo)
    if not re.fullmatch(r"[0-9]{11}", cuit.strip()):
        raise RegistroInvalido("El CUIT debe tener 11 dígitos.", "cuit")
    try:
        validar_password(password)
    except ValueError as e:
        raise RegistroInvalido(str(e), "pass")


def _verificar_disponibles(conn, email, cuit):
    if conn.execute("SELECT 1 FROM administrador WHERE email = %s", (email,)).fetchone():
        raise RegistroInvalido("Ese email ya está registrado.", "email")
    if conn.execute("SELECT 1 FROM organizacion WHERE cuit = %s", (cuit,)).fetchone():
        raise RegistroInvalido("Este CUIT ya está registrado.", "cuit")


def pedir_codigo(nombre, apellido, email, password, organizacion, cuit) -> None:
    email = normalizar_email(email)
    cuit = cuit.strip()
    _validar_datos(nombre, apellido, email, password, organizacion, cuit)

    codigo = f"{secrets.randbelow(1_000_000):06d}"
    with _conectar() as conn:
        _verificar_disponibles(conn, email, cuit)
        conn.execute(
            "UPDATE codigo_administrador SET estado = 'reemplazado' "
            "WHERE email = %s AND proposito = 'registro' AND estado = 'pendiente'",
            (email,),
        )
        conn.execute(
            """
            INSERT INTO codigo_administrador (email, proposito, hash_codigo, vence_en)
            VALUES (%s, 'registro', %s, now() + make_interval(mins => %s))
            """,
            (email, _hash_codigo(email, codigo), MINUTOS_VALIDEZ_CODIGO),
        )

    # TODO: reemplazar por el envío real de email cuando se defina el servicio.
    print(f"[registro] Código de verificación para {email}: {codigo}", flush=True)


def confirmar_codigo(nombre, apellido, email, password, organizacion, cuit, codigo) -> dict:
    email = normalizar_email(email)
    cuit = cuit.strip()
    _validar_datos(nombre, apellido, email, password, organizacion, cuit)

    try:
        with _conectar() as conn:
            fila = conn.execute(
                """
                SELECT id, hash_codigo, intentos, vence_en > now()
                FROM codigo_administrador
                WHERE email = %s AND proposito = 'registro' AND estado = 'pendiente'
                ORDER BY emitido_en DESC LIMIT 1
                FOR UPDATE
                """,
                (email,),
            ).fetchone()
            if fila is None:
                raise RegistroInvalido("Primero solicite un código.", "codigo")
            id_codigo, hash_guardado, intentos, vigente = fila
            if not vigente:
                raise RegistroInvalido("El código expiró. Genere un nuevo código.", "codigo")
            if intentos >= MAX_INTENTOS:
                raise RegistroInvalido(
                    "Ha alcanzado el límite de intentos. Reinicie el registro.", reinicio=True
                )

            if not secrets.compare_digest(hash_guardado, _hash_codigo(email, codigo.strip())):
                conn.execute("UPDATE codigo_administrador SET intentos = intentos + 1 WHERE id = %s", (id_codigo,))
                conn.commit()  # el intento fallido se guarda aunque falle la operación
                restantes = MAX_INTENTOS - intentos - 1
                if restantes <= 0:
                    raise RegistroInvalido(
                        "Ha alcanzado el límite de intentos. Reinicie el registro.", reinicio=True
                    )
                raise RegistroInvalido(f"El código es incorrecto. {restantes} intentos restantes.", "codigo")

            _verificar_disponibles(conn, email, cuit)
            org_id = conn.execute(
                "INSERT INTO organizacion (nombre, cuit) VALUES (%s, %s) RETURNING id",
                (organizacion.strip(), cuit),
            ).fetchone()[0]
            admin_id = conn.execute(
                """
                INSERT INTO administrador (organizacion_id, nombre, apellido, email, hash_contrasena)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
                """,
                (org_id, nombre.strip(), apellido.strip(), email, _hasher.hash(password)),
            ).fetchone()[0]
            conn.execute("UPDATE codigo_administrador SET estado = 'usado' WHERE id = %s", (id_codigo,))
    except psycopg.errors.UniqueViolation:
        raise RegistroInvalido("El email o el CUIT ya no están disponibles.", reinicio=True)

    return {"id": str(admin_id), "email": email, "organizacion_id": str(org_id)}
