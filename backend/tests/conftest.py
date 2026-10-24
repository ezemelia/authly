import pytest
from fastapi.testclient import TestClient

from main import app
from app.database import obtener_conexion
from app.services import registro

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
        conn.execute("DELETE FROM codigo_administrador WHERE email LIKE %s", (f"%{DOMINIO_TEST}",))
        conn.execute("DELETE FROM aplicacion WHERE organizacion_id = ANY(%s)", (orgs,))
        conn.execute("DELETE FROM administrador WHERE organizacion_id = ANY(%s)", (orgs,))
        conn.execute("DELETE FROM organizacion WHERE id = ANY(%s)", (orgs,))


@pytest.fixture(autouse=True)
def limpiar_datos_de_prueba(monkeypatch):
    # el código de verificación queda fijo para poder confirmarlo sin leer el email
    monkeypatch.setattr(registro.secrets, "randbelow", lambda n: int(CODIGO))
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
