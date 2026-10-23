from datetime import datetime, timedelta, timezone

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app import config
from app.database import obtener_conexion
from tests.conftest import ADMIN, CODIGO, DOMINIO_TEST, PREFIJO_CUIT, client, headers_de, registrar_admin


# ---------- /register/codigo ----------

def test_pedir_codigo_ok():
    r = client.post("/register/codigo", json=ADMIN)

    assert r.status_code == 200


def test_pedir_codigo_guarda_el_codigo_hasheado():
    client.post("/register/codigo", json=ADMIN)

    with obtener_conexion() as conn:
        guardado = conn.execute(
            "SELECT hash_codigo, estado FROM codigo_administrador WHERE email = %s", (ADMIN["email"],)
        ).fetchone()
    assert guardado[0] != CODIGO  # no se guarda el código en texto plano
    assert guardado[1] == "pendiente"


def test_pedir_otro_codigo_reemplaza_al_anterior():
    client.post("/register/codigo", json=ADMIN)
    client.post("/register/codigo", json=ADMIN)

    with obtener_conexion() as conn:
        estados = [
            f[0]
            for f in conn.execute(
                "SELECT estado FROM codigo_administrador WHERE email = %s ORDER BY emitido_en",
                (ADMIN["email"],),
            ).fetchall()
        ]
    assert estados == ["reemplazado", "pendiente"]


def test_pedir_codigo_cuit_invalido_devuelve_400_con_el_campo():
    r = client.post("/register/codigo", json={**ADMIN, "cuit": "123"})

    assert r.status_code == 400
    assert r.json()["campo"] == "cuit"


def test_pedir_codigo_password_debil_devuelve_400():
    r = client.post("/register/codigo", json={**ADMIN, "password": "abc"})

    assert r.status_code == 400
    assert r.json()["campo"] == "pass"


def test_pedir_codigo_email_con_formato_invalido_devuelve_422():
    r = client.post("/register/codigo", json={**ADMIN, "email": "malo"})

    assert r.status_code == 422


def test_pedir_codigo_email_ya_registrado_devuelve_400_en_email():
    registrar_admin()
    r = client.post("/register/codigo", json={**ADMIN, "cuit": f"{PREFIJO_CUIT}2"})

    assert r.status_code == 400
    assert r.json()["campo"] == "email"


def test_pedir_codigo_cuit_ya_registrado_devuelve_400_en_cuit():
    registrar_admin()
    r = client.post("/register/codigo", json={**ADMIN, "email": f"otra{DOMINIO_TEST}"})

    assert r.status_code == 400
    assert r.json()["campo"] == "cuit"


# ---------- /register/confirmar ----------

def test_confirmar_ok_crea_organizacion_y_administrador():
    r = registrar_admin()

    assert r.status_code == 201
    assert r.json()["email"] == ADMIN["email"]
    assert "password" not in r.json()


def test_confirmar_guarda_el_email_en_minusculas_y_la_password_hasheada():
    registrar_admin(email=f"ANA{DOMINIO_TEST}")

    with obtener_conexion() as conn:
        email, hash_guardado = conn.execute(
            "SELECT email, hash_contrasena FROM administrador WHERE email LIKE %s", (f"%{DOMINIO_TEST}",)
        ).fetchone()
    assert email == ADMIN["email"]
    assert hash_guardado != ADMIN["password"]
    assert hash_guardado.startswith("$argon2")


def test_confirmar_sin_pedir_codigo_devuelve_400():
    r = client.post("/register/confirmar", json={**ADMIN, "codigo": CODIGO})

    assert r.status_code == 400
    assert r.json()["campo"] == "codigo"


def test_confirmar_con_codigo_incorrecto_informa_intentos_restantes():
    client.post("/register/codigo", json=ADMIN)
    r = client.post("/register/confirmar", json={**ADMIN, "codigo": "000000"})

    assert r.status_code == 400
    assert r.json()["campo"] == "codigo"
    assert "4 intentos" in r.json()["detail"]


def test_confirmar_tras_cinco_intentos_fallidos_pide_reiniciar():
    client.post("/register/codigo", json=ADMIN)
    for _ in range(4):
        client.post("/register/confirmar", json={**ADMIN, "codigo": "000000"})
    r = client.post("/register/confirmar", json={**ADMIN, "codigo": "000000"})

    assert r.json()["reinicio"] is True
    # ya con el código correcto no deja registrar
    r = client.post("/register/confirmar", json={**ADMIN, "codigo": CODIGO})
    assert r.status_code == 400
    assert r.json()["reinicio"] is True


def test_confirmar_con_codigo_vencido_devuelve_400():
    client.post("/register/codigo", json=ADMIN)
    with obtener_conexion() as conn:
        conn.execute(
            "UPDATE codigo_administrador SET emitido_en = now() - interval '2 hours', "
            "vence_en = now() - interval '1 hour' WHERE email = %s",
            (ADMIN["email"],),
        )
    r = client.post("/register/confirmar", json={**ADMIN, "codigo": CODIGO})

    assert r.status_code == 400
    assert "expiró" in r.json()["detail"]


def test_un_codigo_usado_no_sirve_de_nuevo():
    registrar_admin()
    r = client.post("/register/confirmar", json={**ADMIN, "codigo": CODIGO})

    assert r.status_code == 400


# ---------- /login ----------

def test_login_ok_devuelve_token():
    registrar_admin()
    r = client.post("/login", json={"email": ADMIN["email"], "password": ADMIN["password"]})

    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_acepta_el_email_con_mayusculas():
    registrar_admin()
    r = client.post("/login", json={"email": f"ANA{DOMINIO_TEST}", "password": ADMIN["password"]})

    assert r.status_code == 200


def test_login_password_incorrecta_devuelve_401():
    registrar_admin()
    r = client.post("/login", json={"email": ADMIN["email"], "password": "Incorrecta1!"})

    assert r.status_code == 401


def test_login_email_inexistente_devuelve_401():
    r = client.post("/login", json={"email": f"nadie{DOMINIO_TEST}", "password": "Abcdefgh1!"})

    assert r.status_code == 401


def test_login_no_revela_si_el_email_existe():
    registrar_admin()
    mala_password = client.post("/login", json={"email": ADMIN["email"], "password": "Incorrecta1!"})
    no_existe = client.post("/login", json={"email": f"nadie{DOMINIO_TEST}", "password": "Incorrecta1!"})

    assert mala_password.json() == no_existe.json()


# ---------- /me ----------

def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_me_con_token_valido_devuelve_los_datos_del_administrador():
    r = client.get("/me", headers=headers_de())

    assert r.status_code == 200
    assert r.json()["email"] == ADMIN["email"]
    assert r.json()["nombre"] == ADMIN["nombre"]
    assert "organizacion_id" in r.json()
    assert "hash_contrasena" not in r.json()


def test_me_sin_token_devuelve_401():
    assert client.get("/me").status_code == 401


def test_me_con_token_inventado_devuelve_401():
    assert client.get("/me", headers=_headers("esto-no-es-un-token")).status_code == 401


def test_me_con_token_firmado_con_otra_clave_devuelve_401():
    # alguien intenta falsificar un token con su propio par de claves, sin conocer la privada real
    otra_privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = otra_privada.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    falso = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, pem, algorithm="RS256"
    )

    assert client.get("/me", headers=_headers(falso)).status_code == 401


def test_me_con_token_vencido_devuelve_401():
    registrar_admin()
    with obtener_conexion() as conn:
        id_admin = conn.execute(
            "SELECT id FROM administrador WHERE email = %s", (ADMIN["email"],)
        ).fetchone()[0]
    vencido = jwt.encode(
        {"sub": str(id_admin), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        config.JWT_PRIVATE_KEY,
        algorithm="RS256",
    )

    assert client.get("/me", headers=_headers(vencido)).status_code == 401


def test_me_con_token_de_administrador_borrado_devuelve_401():
    headers = headers_de()
    with obtener_conexion() as conn:
        conn.execute("DELETE FROM administrador WHERE email = %s", (ADMIN["email"],))

    assert client.get("/me", headers=headers).status_code == 401
