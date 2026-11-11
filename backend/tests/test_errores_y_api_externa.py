import jwt

from app import config
from tests.conftest import CERO, CODIGO, DOMINIO_TEST, client, crear_app, crear_rol, headers_de, insertar_usuario


# ---------- formato de error unificado (panel) ----------

def test_los_errores_del_panel_traen_detail_campo_y_reinicio():
    headers = headers_de()
    crear_app(headers, "Mi app")

    duplicada = client.post("/platform/applications/", json={"nombre": "MI APP"}, headers=headers)
    inexistente = client.post(f"/platform/applications/{CERO}/regenerar-secret", headers=headers)

    assert duplicada.status_code == 409
    assert duplicada.json() == {
        "detail": "Ya existe una aplicación con el nombre 'MI APP'.", "campo": "nombre", "reinicio": False,
    }
    assert inexistente.status_code == 404
    assert inexistente.json()["campo"] == "general"
    assert inexistente.json()["motivo"] == "aplicacion-inexistente"


def test_nombre_de_aplicacion_vacio_devuelve_400_en_el_campo_nombre():
    r = client.post("/platform/applications/", json={"nombre": "  "}, headers=headers_de())

    assert r.status_code == 400
    assert r.json()["campo"] == "nombre"


def test_eliminar_aplicacion_con_usuarios_informa_la_cantidad():
    headers = headers_de()
    cid = crear_app(headers)["client_id"]
    rol = crear_rol(headers, cid, "Lector")
    insertar_usuario(cid, "Ana", "Paz", f"ana{DOMINIO_TEST}", [rol["id"]])

    r = client.delete(f"/platform/applications/{cid}", headers=headers)

    assert r.status_code == 409
    assert r.json()["motivo"] == "tiene-usuarios"
    assert r.json()["cantidad_usuarios"] == 1


def test_el_error_de_autenticacion_del_panel_tambien_trae_el_formato():
    r = client.get("/platform/applications/")

    assert r.status_code == 401
    assert r.json()["campo"] == "general"
    assert r.json()["reinicio"] is False


def test_la_api_externa_conserva_su_formato_de_error():
    r = client.post(
        "/auth/login", json={"email": "a@b.com", "password": "x"}, headers={"X-Client-Id": CERO, "X-Client-Secret": "x"}
    )

    assert r.status_code == 401
    assert set(r.json()) == {"detail"}  # sin campo ni reinicio


# ---------- API externa: registro y login de usuario de una aplicación (CU-05 y CU-07) ----------

USUARIO = {"nombre": "Luis", "apellido": "Ferreyra", "email": f"luis{DOMINIO_TEST}", "password": "Abcdefgh1!"}


def _app_lista():
    headers = headers_de()
    app = crear_app(headers)
    crear_rol(headers, app["client_id"], "Lector", por_defecto=True)
    return headers, app, {"X-Client-Id": app["client_id"], "X-Client-Secret": app["client_secret"]}


def test_registro_de_usuario_por_api_le_asigna_el_rol_por_defecto():
    headers, app, credenciales = _app_lista()

    paso1 = client.post("/auth/register", json=USUARIO, headers=credenciales)
    paso2 = client.post("/auth/register/verify", json={**USUARIO, "codigo": CODIGO}, headers=credenciales)

    assert paso1.status_code == 201
    assert paso2.status_code == 200
    usuarios = client.get(f"/platform/applications/{app['client_id']}/users/", headers=headers).json()["usuarios"]
    assert [(u["email"], [r["nombre"] for r in u["roles"]]) for u in usuarios] == [(USUARIO["email"], ["Lector"])]


def test_el_usuario_registrado_por_api_puede_iniciar_sesion():
    _, app, credenciales = _app_lista()
    client.post("/auth/register", json=USUARIO, headers=credenciales)
    client.post("/auth/register/verify", json={**USUARIO, "codigo": CODIGO}, headers=credenciales)

    r = client.post("/auth/login", json={"email": USUARIO["email"], "password": USUARIO["password"]}, headers=credenciales)

    assert r.status_code == 200
    payload = jwt.decode(r.json()["access_token"], config.JWT_PUBLIC_KEY, algorithms=["RS256"])
    assert payload["type"] == "user"
    assert payload["app_id"] == app["client_id"]  # texto, no UUID
    assert payload["roles"] == ["Lector"]


def test_login_de_usuario_con_credenciales_de_aplicacion_incorrectas_devuelve_401():
    _, app, _ = _app_lista()

    r = client.post(
        "/auth/login",
        json={"email": USUARIO["email"], "password": USUARIO["password"]},
        headers={"X-Client-Id": app["client_id"], "X-Client-Secret": "incorrecto"},
    )

    assert r.status_code == 401


def test_registro_sin_rol_por_defecto_devuelve_422():
    headers = headers_de()
    app = crear_app(headers)
    credenciales = {"X-Client-Id": app["client_id"], "X-Client-Secret": app["client_secret"]}
    client.post("/auth/register", json=USUARIO, headers=credenciales)

    r = client.post("/auth/register/verify", json={**USUARIO, "codigo": CODIGO}, headers=credenciales)

    assert r.status_code == 422


def test_el_mismo_email_se_puede_registrar_en_otra_aplicacion():
    headers, _, credenciales = _app_lista()
    otra = crear_app(headers, "Otra app")
    crear_rol(headers, otra["client_id"], "Lector", por_defecto=True)
    otras = {"X-Client-Id": otra["client_id"], "X-Client-Secret": otra["client_secret"]}
    client.post("/auth/register", json=USUARIO, headers=credenciales)
    client.post("/auth/register/verify", json={**USUARIO, "codigo": CODIGO}, headers=credenciales)

    r = client.post("/auth/register", json=USUARIO, headers=otras)

    assert r.status_code == 201
