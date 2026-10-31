import re

import psycopg
from argon2 import PasswordHasher

from app.database import obtener_conexion
from app.services.verification import (
    CodigoIncorrecto, CodigoInexistente, CodigoVencido, ErrorEnvioCodigo, IntentosAgotados,
    LimiteCodigosExcedido, generar_codigo, validar_codigo,
)
from app.utils.validators import normalizar_email, validar_password

_hasher = PasswordHasher()


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

    with _conectar() as conn:
        _verificar_disponibles(conn, email, cuit)

    try:
        generar_codigo(email, "registro")
    except LimiteCodigosExcedido as e:
        raise RegistroInvalido(str(e))
    except ErrorEnvioCodigo as e:
        raise RegistroInvalido(str(e))


def confirmar_codigo(nombre, apellido, email, password, organizacion, cuit, codigo) -> dict:
    email = normalizar_email(email)
    cuit = cuit.strip()
    _validar_datos(nombre, apellido, email, password, organizacion, cuit)

    try:
        with _conectar() as conn:
            try:
                validar_codigo(email, codigo, "registro", conn=conn)
            except (CodigoInexistente, CodigoVencido, CodigoIncorrecto) as e:
                raise RegistroInvalido(str(e), "codigo")
            except IntentosAgotados as e:
                raise RegistroInvalido(f"{e} Reinicie el registro.", reinicio=True)

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
    except psycopg.errors.UniqueViolation:
        raise RegistroInvalido("El email o el CUIT ya no están disponibles.", reinicio=True)

    return {"id": str(admin_id), "email": email, "organizacion_id": str(org_id)}
