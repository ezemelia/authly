import pytest
from fastapi.testclient import TestClient

from main import app
from app.database import obtener_conexion
from app.services import verification

# Estos tests usan la base de datos real (Supabase), así que todo lo que crean se puede
# reconocer y borrar: emails que terminan en DOMINIO_TEST y CUITs que empiezan con PREFIJO_CUIT.
DOMINIO_TEST = "@test-authly.com"
PREFIJO_CUIT = "9999999999"

ADMIN = {
    "nombre": "Ana",
    "apellido": "Pérez",
    "email": f"ana{DOMINIO_TEST}",
    "password": "Abcdefgh1!",
    "organizacion": "Org de prueba",
    "cuit": f"{PREFIJO_CUIT}1",
}
CODIGO = "123456"

client = TestClient(app)
emails_enviados = []


def _borrar_datos_de_prueba():
    with obtener_conexion() as conn:
        orgs = [
            f[0]
            for f in conn.execute(
                """
                SELECT id FROM organizacion WHERE cuit LIKE %s
                UNION
                SELECT organizacion_id FROM administrador WHERE email LIKE %s
                """,
                (f"{PREFIJO_CUIT}%", f"%{DOMINIO_TEST}"),
            ).fetchall()
        ]
        apps = [f[0] for f in conn.execute(
            "SELECT client_id FROM aplicacion WHERE organizacion_id = ANY(%s)", (orgs,)
        ).fetchall()]
        conn.execute("DELETE FROM codigo_administrador WHERE email LIKE %s", (f"%{DOMINIO_TEST}",))
        conn.execute("DELETE FROM codigo_usuario WHERE email LIKE %s", (f"%{DOMINIO_TEST}",))
        # los usuarios y sus roles van antes que la aplicación (la base no deja borrar una aplicación con usuarios)
        conn.execute("DELETE FROM usuario_rol WHERE aplicacion_id = ANY(%s)", (apps,))
        conn.execute("DELETE FROM usuario WHERE aplicacion_id = ANY(%s)", (apps,))
        conn.execute("DELETE FROM aplicacion WHERE organizacion_id = ANY(%s)", (orgs,))
        conn.execute("DELETE FROM administrador WHERE organizacion_id = ANY(%s)", (orgs,))
        conn.execute("DELETE FROM organizacion WHERE id = ANY(%s)", (orgs,))


@pytest.fixture(autouse=True)
def limpiar_datos_de_prueba(monkeypatch):
    # el código de verificación queda fijo para poder confirmarlo sin leer el email,
    # y los emails no se envían: se guardan en `emails_enviados`
    monkeypatch.setattr(verification.secrets, "randbelow", lambda n: int(CODIGO))
    emails_enviados.clear()
    monkeypatch.setattr(
        verification, "_enviar_email", lambda email, codigo, proposito: emails_enviados.append((email, codigo, proposito))
    )
    _borrar_datos_de_prueba()
    yield
    _borrar_datos_de_prueba()


def registrar_admin(**cambios):
    datos = {**ADMIN, **cambios}
    client.post("/register/codigo", json=datos)
    return client.post("/register/confirmar", json={**datos, "codigo": CODIGO})


def headers_de(admin=ADMIN):
    registrar_admin(**{k: admin[k] for k in admin})
    token = client.post(
        "/login", json={"email": admin["email"], "password": admin["password"]}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


OTRO_ADMIN = {**ADMIN, "email": f"bruno{DOMINIO_TEST}", "cuit": f"{PREFIJO_CUIT}2", "organizacion": "Otra org"}
CERO = "00000000-0000-0000-0000-000000000000"


def crear_app(headers, nombre="App de prueba"):
    """Devuelve {nombre, client_id, client_secret}."""
    return client.post("/platform/applications/", json={"nombre": nombre}, headers=headers).json()


def crear_rol(headers, client_id, nombre, por_defecto=False, permisos=()):
    r = client.post(
        f"/platform/applications/{client_id}/roles/",
        json={"nombre": nombre, "por_defecto": por_defecto, "permisos": list(permisos)},
        headers=headers,
    )
    return r.json()["rol"]


def insertar_usuario(client_id, nombre, apellido, email, roles):
    """Crea un usuario directo en la base (el panel no crea usuarios: se registran por la API, CU-05)."""
    with obtener_conexion() as conn:
        usuario_id = conn.execute(
            "INSERT INTO usuario (aplicacion_id, nombre, apellido, email, hash_contrasena) "
            "VALUES (%s, %s, %s, %s, 'hash-de-prueba') RETURNING id",
            (client_id, nombre, apellido, email),
        ).fetchone()[0]
        for rol_id in roles:
            conn.execute(
                "INSERT INTO usuario_rol (usuario_id, rol_id, aplicacion_id) VALUES (%s, %s, %s)",
                (usuario_id, rol_id, client_id),
            )
    return str(usuario_id)
