from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from main import app
from app import config
from app.database import obtener_conexion

# Estos tests usan la base de datos real (authly_dev), así que el contenedor debe estar corriendo.
# Todos los emails de prueba terminan igual, para poder borrarlos sin tocar otros usuarios.
DOMINIO_TEST = "@test-authly.com"
USUARIO = {"username": "ana", "email": f"ana{DOMINIO_TEST}", "password": "Abcdefgh1!"}

client = TestClient(app)


@pytest.fixture(autouse=True)
def limpiar_usuarios_de_prueba():
    # autouse: corre alrededor de cada test; borra antes y después para empezar siempre limpio
    def borrar():
        with obtener_conexion() as conn:
            conn.execute("DELETE FROM users WHERE email LIKE %s", (f"%{DOMINIO_TEST}",))

    borrar()
    yield  # acá se ejecuta el test
    borrar()


# ---------- /register ----------

def test_register_ok_devuelve_201_y_no_expone_la_password():
    r = client.post("/register", json=USUARIO)

    assert r.status_code == 201
    assert r.json()["email"] == USUARIO["email"]
    assert "password" not in r.json()
    assert "password_hash" not in r.json()


def test_register_guarda_el_email_en_minusculas():
    r = client.post("/register", json={**USUARIO, "email": f"ANA{DOMINIO_TEST}"})

    assert r.json()["email"] == f"ana{DOMINIO_TEST}"


def test_register_guarda_la_password_hasheada():
    client.post("/register", json=USUARIO)

    with obtener_conexion() as conn:
        guardado = conn.execute(
            "SELECT password_hash FROM users WHERE email = %s", (USUARIO["email"],)
        ).fetchone()[0]
    assert guardado != USUARIO["password"]   # no se guardó en texto plano
    assert guardado.startswith("$2b$")       # formato de bcrypt


def test_register_email_repetido_devuelve_409():
    client.post("/register", json=USUARIO)
    r = client.post("/register", json=USUARIO)

    assert r.status_code == 409


def test_register_email_repetido_con_otras_mayusculas_devuelve_409():
    client.post("/register", json=USUARIO)
    r = client.post("/register", json={**USUARIO, "email": f"ANA{DOMINIO_TEST}"})

    assert r.status_code == 409


def test_register_password_debil_devuelve_400():
    r = client.post("/register", json={**USUARIO, "password": "abc"})

    assert r.status_code == 400


def test_register_email_con_formato_invalido_devuelve_422():
    r = client.post("/register", json={**USUARIO, "email": "malo"})

    assert r.status_code == 422


# ---------- /login ----------

def test_login_ok_devuelve_token():
    client.post("/register", json=USUARIO)
    r = client.post("/login", json={"email": USUARIO["email"], "password": USUARIO["password"]})

    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]  # no está vacío


def test_login_acepta_el_email_con_mayusculas():
    client.post("/register", json=USUARIO)
    r = client.post("/login", json={"email": f"ANA{DOMINIO_TEST}", "password": USUARIO["password"]})

    assert r.status_code == 200


def test_login_password_incorrecta_devuelve_401():
    client.post("/register", json=USUARIO)
    r = client.post("/login", json={"email": USUARIO["email"], "password": "Incorrecta1!"})

    assert r.status_code == 401


def test_login_email_inexistente_devuelve_401():
    r = client.post("/login", json={"email": f"nadie{DOMINIO_TEST}", "password": "Abcdefgh1!"})

    assert r.status_code == 401


def test_login_no_revela_si_el_email_existe():
    # mismo mensaje para "email inexistente" y "password incorrecta"
    client.post("/register", json=USUARIO)
    mala_password = client.post("/login", json={"email": USUARIO["email"], "password": "Incorrecta1!"})
    no_existe = client.post("/login", json={"email": f"nadie{DOMINIO_TEST}", "password": "Incorrecta1!"})

    assert mala_password.json() == no_existe.json()


# ---------- /me ----------

def _token_de_usuario_registrado():
    client.post("/register", json=USUARIO)
    r = client.post("/login", json={"email": USUARIO["email"], "password": USUARIO["password"]})
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_me_con_token_valido_devuelve_los_datos_del_usuario():
    r = client.get("/me", headers=_headers(_token_de_usuario_registrado()))

    assert r.status_code == 200
    assert r.json()["email"] == USUARIO["email"]
    assert r.json()["username"] == USUARIO["username"]
    assert "password_hash" not in r.json()


def test_me_sin_token_devuelve_401():
    r = client.get("/me")

    assert r.status_code == 401


def test_me_con_token_inventado_devuelve_401():
    r = client.get("/me", headers=_headers("esto-no-es-un-token"))

    assert r.status_code == 401


def test_me_con_token_firmado_con_otra_clave_devuelve_401():
    # alguien intenta falsificar un token con su propio par de claves, sin conocer la privada real
    otra_privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = otra_privada.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    falso = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        pem,
        algorithm="RS256",
    )
    r = client.get("/me", headers=_headers(falso))

    assert r.status_code == 401


def test_me_con_token_vencido_devuelve_401():
    client.post("/register", json=USUARIO)
    with obtener_conexion() as conn:
        id_usuario = conn.execute(
            "SELECT id FROM users WHERE email = %s", (USUARIO["email"],)
        ).fetchone()[0]
    # token bien firmado pero que venció hace un minuto
    vencido = jwt.encode(
        {"sub": str(id_usuario), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        config.JWT_PRIVATE_KEY,
        algorithm="RS256",
    )
    r = client.get("/me", headers=_headers(vencido))

    assert r.status_code == 401


def test_me_con_token_de_usuario_borrado_devuelve_401():
    token = _token_de_usuario_registrado()
    with obtener_conexion() as conn:
        conn.execute("DELETE FROM users WHERE email = %s", (USUARIO["email"],))
    r = client.get("/me", headers=_headers(token))

    assert r.status_code == 401
