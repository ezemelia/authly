"""Servicio compartido de códigos de verificación (registro y recuperación).

- Administradores (app_id=None): tabla codigo_administrador (CU-01).
- Usuarios de una aplicación (app_id=<client_id>): tabla codigo_usuario (CU-05, CU-11).
"""
import hashlib
import hmac
import os
import secrets
import smtplib
from email.message import EmailMessage

from app.database import obtener_conexion
from app.utils.validators import normalizar_email

MINUTOS_VALIDEZ = 10
MAX_CODIGOS_POR_HORA = 3
MAX_INTENTOS = 5
PROPOSITOS = ("registro", "recuperacion")

_TABLAS = {False: "codigo_administrador", True: "codigo_usuario"}


class LimiteCodigosExcedido(Exception):
    pass


class CodigoInexistente(Exception):
    pass


class CodigoVencido(Exception):
    pass


class CodigoIncorrecto(Exception):
    def __init__(self, intentos_restantes: int):
        super().__init__(f"El código es incorrecto. {intentos_restantes} intentos restantes.")
        self.intentos_restantes = intentos_restantes


class IntentosAgotados(Exception):
    pass


class ErrorEnvioCodigo(Exception):
    pass


def _conectar():
    conexion = obtener_conexion()
    if conexion is None:
        raise RuntimeError("No se pudo conectar a la base de datos")
    return conexion


def _hash_codigo(email: str, codigo: str, proposito: str, app_id) -> str:
    # HMAC con una clave que NO está en la base: solo hay un millón de códigos posibles,
    # así que sin la clave una filtración de la base no permite recuperarlos probando.
    clave = os.environ.get("CODIGO_HMAC_KEY")
    if not clave:
        raise RuntimeError("Falta la variable de entorno CODIGO_HMAC_KEY")
    mensaje = f"{app_id or ''}:{proposito}:{email}:{codigo}"
    return hmac.new(clave.encode(), mensaje.encode(), hashlib.sha256).hexdigest()


def _filtro(app_id):
    """Devuelve (tabla, condición SQL, parámetros) para email + propósito (+ aplicación)."""
    tabla = _TABLAS[app_id is not None]
    condicion = "email = %s AND proposito = %s"
    if app_id is not None:
        condicion += " AND aplicacion_id = %s"
    return tabla, condicion


def _params(email, proposito, app_id):
    return (email, proposito) if app_id is None else (email, proposito, str(app_id))


def _enviar_email(email: str, codigo: str, proposito: str) -> None:
    asunto = "Código de verificación" if proposito == "registro" else "Código para recuperar tu contraseña"
    mensaje = EmailMessage()
    mensaje["From"] = os.environ.get("SMTP_FROM", "no-reply@authly.local")
    mensaje["To"] = email
    mensaje["Subject"] = f"Authly: {asunto}"
    mensaje.set_content(
        f"Tu código es: {codigo}\n\nVence en {MINUTOS_VALIDEZ} minutos. "
        "Si no lo pediste, ignorá este mensaje."
    )
    host = os.environ.get("SMTP_HOST", "localhost")
    puerto = int(os.environ.get("SMTP_PORT", "1025"))
    with smtplib.SMTP(host, puerto, timeout=10) as smtp:
        if os.environ.get("SMTP_USER"):
            smtp.starttls()
            smtp.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASSWORD", ""))
        smtp.send_message(mensaje)


def generar_codigo(email: str, proposito: str, app_id=None) -> None:
    """Genera un código de 6 dígitos, lo guarda hasheado (vence en 10 min) y lo envía por email.

    Lanza LimiteCodigosExcedido (máx. 3 por hora por email + propósito + app) o ErrorEnvioCodigo.
    """
    if proposito not in PROPOSITOS:
        raise ValueError(f"Propósito inválido: {proposito}")
    email = normalizar_email(email)
    tabla, condicion = _filtro(app_id)
    params = _params(email, proposito, app_id)
    codigo = f"{secrets.randbelow(1_000_000):06d}"

    # orden indicado por la guía de la base: comprobar límite, limpiar, reemplazar, insertar
    with _conectar() as conn:
        emitidos = conn.execute(
            f"SELECT count(*) FROM {tabla} WHERE {condicion} AND emitido_en > now() - interval '1 hour'",
            params,
        ).fetchone()[0]
        if emitidos >= MAX_CODIGOS_POR_HORA:
            raise LimiteCodigosExcedido("Ha superado el límite de códigos. Intente nuevamente más tarde.")

        conn.execute(f"DELETE FROM {tabla} WHERE emitido_en < now() - interval '1 hour'")
        conn.execute(
            f"UPDATE {tabla} SET estado = 'reemplazado' WHERE {condicion} AND estado = 'pendiente'", params
        )
        columnas = "email, proposito, hash_codigo, vence_en"
        marcas = "%s, %s, %s, now() + make_interval(mins => %s)"
        valores = [email, proposito, _hash_codigo(email, codigo, proposito, app_id), MINUTOS_VALIDEZ]
        if app_id is not None:
            columnas += ", aplicacion_id"
            marcas += ", %s"
            valores.append(str(app_id))
        conn.execute(f"INSERT INTO {tabla} ({columnas}) VALUES ({marcas})", valores)

    # el envío va después del commit: si falla, el código queda guardado pero la persona pide otro
    try:
        _enviar_email(email, codigo, proposito)
    except Exception as e:
        raise ErrorEnvioCodigo("No se pudo enviar el correo.") from e


def _validar(conn, email, codigo, proposito, app_id) -> None:
    tabla, condicion = _filtro(app_id)
    fila = conn.execute(
        f"""
        SELECT id, hash_codigo, intentos, vence_en > now()
        FROM {tabla}
        WHERE {condicion} AND estado = 'pendiente'
        ORDER BY emitido_en DESC LIMIT 1
        FOR UPDATE
        """,
        _params(email, proposito, app_id),
    ).fetchone()
    if fila is None:
        raise CodigoInexistente("Primero solicite un código.")
    id_codigo, hash_guardado, intentos, vigente = fila

    if not vigente:
        raise CodigoVencido("El código expiró. Genere un nuevo código.")
    if intentos >= MAX_INTENTOS:
        raise IntentosAgotados("Ha alcanzado el límite de intentos.")

    if not hmac.compare_digest(hash_guardado, _hash_codigo(email, codigo.strip(), proposito, app_id)):
        conn.execute(f"UPDATE {tabla} SET intentos = intentos + 1 WHERE id = %s", (id_codigo,))
        conn.commit()  # el intento fallido se guarda aunque la operación que sigue se deshaga
        restantes = MAX_INTENTOS - intentos - 1
        if restantes <= 0:
            raise IntentosAgotados("Ha alcanzado el límite de intentos.")
        raise CodigoIncorrecto(restantes)

    conn.execute(f"UPDATE {tabla} SET estado = 'usado' WHERE id = %s", (id_codigo,))


def validar_codigo(email: str, codigo: str, proposito: str, app_id=None, conn=None) -> None:
    """Verifica el código y lo marca como usado. No devuelve nada si es correcto.

    Lanza CodigoInexistente, CodigoVencido, CodigoIncorrecto o IntentosAgotados.

    conn: conexión opcional. Si se pasa, el "usado" queda dentro de la transacción del llamador
    (para hacerlo junto con otra escritura, como crear la cuenta) y no se hace commit al final.
    Un intento fallido sí se confirma siempre, así no se pierde si el llamador hace rollback.
    """
    email = normalizar_email(email)
    if conn is not None:
        _validar(conn, email, codigo, proposito, app_id)
        return
    with _conectar() as propia:
        _validar(propia, email, codigo, proposito, app_id)
