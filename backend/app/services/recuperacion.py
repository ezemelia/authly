"""CU-10: recuperar la contraseña de un administrador (panel)."""
import logging

from argon2 import PasswordHasher

from app.database import obtener_conexion
from app.services.users import _password_correcta
from app.services.verification import (
    CodigoIncorrecto, CodigoInexistente, CodigoVencido, ErrorEnvioCodigo, IntentosAgotados,
    LimiteCodigosExcedido, generar_codigo, validar_codigo,
)
from app.utils.validators import normalizar_email, validar_password

log = logging.getLogger("authly.recuperacion")
_hasher = PasswordHasher()

MENSAJE_GENERICO = "Si el correo corresponde a una cuenta, le enviamos un código."
CODIGO_INVALIDO = "Código inválido o vencido."


class RecuperacionInvalida(Exception):
    def __init__(self, mensaje: str, campo: str = "general"):
        super().__init__(mensaje)
        self.campo = campo


def _conectar():
    conexion = obtener_conexion()
    if conexion is None:
        raise RuntimeError("No se pudo conectar a la base de datos")
    return conexion


def pedir_codigo(email: str) -> None:
    """Siempre termina sin error visible: no revela si el email es de un administrador (AURN-05)."""
    email = normalizar_email(email)
    with _conectar() as conn:
        existe = conn.execute("SELECT 1 FROM administrador WHERE email = %s", (email,)).fetchone()
    if existe is None:
        return  # no se envía nada y se responde igual
    try:
        generar_codigo(email, "recuperacion")
    except LimiteCodigosExcedido:
        log.warning("Recuperación: límite de códigos alcanzado para un administrador")
    except ErrorEnvioCodigo:
        log.error("Recuperación: no se pudo enviar el código", exc_info=True)  # constancia operativa (AURN-10)


def cambiar_password(email: str, codigo: str, password: str) -> None:
    email = normalizar_email(email)

    with _conectar() as conn:
        # sin distinguir la causa (inexistente, vencido, incorrecto o agotado), como pide el CU-10
        try:
            validar_codigo(email, codigo, "recuperacion", conn=conn)
        except (CodigoInexistente, CodigoVencido, CodigoIncorrecto, IntentosAgotados):
            raise RecuperacionInvalida(CODIGO_INVALIDO, "codigo")

        # con el código válido, los problemas de la contraseña NO consumen intentos ni gastan el código:
        # al lanzar la excepción se hace rollback y el código queda como estaba
        try:
            validar_password(password)
        except ValueError as e:
            raise RecuperacionInvalida(str(e), "pass")

        fila = conn.execute("SELECT id, hash_contrasena FROM administrador WHERE email = %s", (email,)).fetchone()
        if fila is None:
            raise RecuperacionInvalida(CODIGO_INVALIDO, "codigo")
        if _password_correcta(password, fila[1]):
            raise RecuperacionInvalida("La contraseña nueva debe ser distinta de la actual.", "pass")

        conn.execute("UPDATE administrador SET hash_contrasena = %s WHERE id = %s", (_hasher.hash(password), fila[0]))
