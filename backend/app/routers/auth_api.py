from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.config import JWT_PUBLIC_KEY
from app.middleware.app_credentials import aplicacion_actual
from app.services.auth import crear_token
from app.services.users import autenticar_usuario_app, CredencialesInvalidas
from app.utils.validators import normalizar_email, validar_password
from app.database import obtener_conexion
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.services.verification import (
    generar_codigo, validar_codigo,
    LimiteCodigosExcedido, ErrorEnvioCodigo,
    CodigoInexistente, CodigoVencido, CodigoIncorrecto, IntentosAgotados,
)

router = APIRouter(prefix="/auth", tags=["API Externa - Auth"])


class LoginUsuarioEntrada(BaseModel):
    email: str
    password: str

class RegistroUsuarioEntrada(BaseModel):
    nombre: str
    apellido: str
    email: str
    password: str

class VerificarRegistroEntrada(BaseModel):
    nombre: str
    apellido: str
    email: str
    password: str
    codigo: str

class RecuperarPasswordEntrada(BaseModel):
    email: str

class ResetearPasswordEntrada(BaseModel):
    email: str
    codigo: str
    new_password: str

@router.get("/public-key")
def obtener_clave_publica():
    """CU-08: Devuelve la clave pública RSA para verificar tokens JWT.
    Endpoint público — no requiere autenticación.
    """
    return {"public_key": JWT_PUBLIC_KEY}


@router.post("/login")
def login_usuario(datos: LoginUsuarioEntrada, app: dict = Depends(aplicacion_actual)):
    try:
        usuario = autenticar_usuario_app(datos.email, datos.password, app["id"])
    except CredencialesInvalidas as e:
        raise HTTPException(status_code=401, detail=str(e))

    # Obtener roles del usuario para hint de UI
    conn = obtener_conexion()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.nombre FROM authly.rol r
                JOIN authly.usuario_rol ur ON ur.rol_id = r.id
                WHERE ur.usuario_id = %s
                """,
                (usuario["id"],),
            )
            roles = [fila[0] for fila in cur.fetchall()]
    finally:
        conn.close()

    token = crear_token({
        "sub": usuario["id"],
        "type": "user",
        "org_id": app["organizacion_id"],
        "app_id": app["id"],
        "roles": roles,
    })

    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 28800,
    }

@router.post("/register", status_code=201)
def registrar_usuario(datos: RegistroUsuarioEntrada, app: dict = Depends(aplicacion_actual)):
    nombre = datos.nombre.strip()
    apellido = datos.apellido.strip()
    if not nombre or not apellido:
        raise HTTPException(status_code=400, detail="Nombre y apellido son obligatorios")

    email = normalizar_email(datos.email)
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email inválido")

    try:
        validar_password(datos.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # verificar que el email no esté registrado en ESTA aplicación
    conn = obtener_conexion()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM authly.usuario WHERE email = %s AND aplicacion_id = %s",
                (email, app["id"]),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="El email ya está registrado en esta aplicación")
    finally:
        conn.close()

    try:
        generar_codigo(email, "registro", app["id"])
    except LimiteCodigosExcedido as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ErrorEnvioCodigo:
        raise HTTPException(status_code=500, detail="No se pudo enviar el código de verificación")

    return {"message": "Se envió código de verificación al email.", "expires_in": 600}

@router.post("/register/verify")
def verificar_registro(datos: VerificarRegistroEntrada, app: dict = Depends(aplicacion_actual)):
    """CU-05 paso 2: Verifica el código y crea el usuario con rol por defecto."""
    nombre = datos.nombre.strip()
    apellido = datos.apellido.strip()
    if not nombre or not apellido:
        raise HTTPException(status_code=400, detail="Nombre y apellido son obligatorios")

    email = normalizar_email(datos.email)
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email inválido")

    try:
        validar_password(datos.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    conn = obtener_conexion()
    if conn is None:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    try:
        # verificar que el email no esté ya registrado en esta app
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM authly.usuario WHERE email = %s AND aplicacion_id = %s",
                (email, app["id"]),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="El email ya está registrado en esta aplicación")

        # buscar rol por defecto de la aplicación
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM authly.rol WHERE aplicacion_id = %s AND por_defecto = true",
                (app["id"],),
            )
            rol = cur.fetchone()
            if rol is None:
                raise HTTPException(status_code=422, detail="La aplicación no tiene rol por defecto configurado")
            rol_id = rol[0]

        # validar código DENTRO de esta transacción
        try:
            validar_codigo(email, datos.codigo, "registro", app["id"], conn=conn)
        except CodigoInexistente as e:
            raise HTTPException(status_code=404, detail=str(e))
        except CodigoVencido as e:
            raise HTTPException(status_code=400, detail=str(e))
        except CodigoIncorrecto as e:
            raise HTTPException(status_code=400, detail=str(e))
        except IntentosAgotados as e:
            raise HTTPException(status_code=400, detail=str(e))

        # crear usuario + asignar rol (atómico)
        from argon2 import PasswordHasher
        hasher = PasswordHasher()
        hash_password = hasher.hash(datos.password)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO authly.usuario (nombre, apellido, email, hash_contrasena, aplicacion_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (nombre, apellido, email, hash_password, app["id"]),
            )
            usuario_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO authly.usuario_rol (usuario_id, rol_id) VALUES (%s, %s)",
                (usuario_id, rol_id),
            )

        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Error interno al crear la cuenta")
    finally:
        conn.close()

    return {"message": "Cuenta verificada exitosamente."}

@router.post("/password/recover")
def recuperar_password(datos: RecuperarPasswordEntrada, app: dict = Depends(aplicacion_actual)):
    """CU-11 paso 1: Envía código de recuperación al email del usuario."""
    email = normalizar_email(datos.email)

    try:
        conn = obtener_conexion()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM authly.usuario WHERE email = %s AND aplicacion_id = %s",
                    (email, app["id"]),
                )
                if cur.fetchone() is None:
                    return {"message": "Si el email está registrado, se envió un código de recuperación."}
        finally:
            conn.close()

        generar_codigo(email, "recuperacion", app["id"])
    except LimiteCodigosExcedido:
        raise HTTPException(status_code=429, detail="Demasiados intentos. Intente más tarde.")
    except ErrorEnvioCodigo:
        raise HTTPException(status_code=500, detail="No se pudo enviar el código.")

    return {"message": "Si el email está registrado, se envió un código de recuperación."}

@router.post("/password/reset")
def resetear_password(datos: ResetearPasswordEntrada, app: dict = Depends(aplicacion_actual)):
    """CU-11 paso 2: Valida el código y actualiza la contraseña."""
    email = normalizar_email(datos.email)
    hasher = PasswordHasher()

    try:
        validar_codigo(email, datos.codigo, "recuperacion", app["id"])
    except CodigoInexistente as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CodigoVencido as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CodigoIncorrecto as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntentosAgotados as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        validar_password(datos.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    conn = obtener_conexion()
    if conn is None:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, hash_contrasena FROM authly.usuario WHERE email = %s AND aplicacion_id = %s",
                (email, app["id"]),
            )
            fila = cur.fetchone()
            if fila is None:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            usuario_id, hash_actual = fila

            try:
                if hasher.verify(hash_actual, datos.new_password):
                    raise HTTPException(status_code=400, detail="La nueva contraseña debe ser diferente a la actual")
            except VerifyMismatchError:
                pass

            cur.execute(
                "UPDATE authly.usuario SET hash_contrasena = %s WHERE id = %s",
                (hasher.hash(datos.new_password), usuario_id),
            )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Error interno al actualizar la contraseña")
    finally:
        conn.close()

    return {"message": "Contraseña actualizada exitosamente."}