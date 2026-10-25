from tests.conftest import ADMIN, DOMINIO_TEST, PREFIJO_CUIT, client, headers_de

URL = "/platform/applications/"
OTRO_ADMIN = {**ADMIN, "email": f"bruno{DOMINIO_TEST}", "cuit": f"{PREFIJO_CUIT}2", "organizacion": "Otra org"}


def test_sin_token_devuelve_401():
    assert client.get(URL).status_code == 401
    assert client.post(URL, json={"nombre": "x"}).status_code == 401


def test_crear_aplicacion_devuelve_client_id_y_secret():
    r = client.post(URL, json={"nombre": "Mi app", "descripcion": "demo"}, headers=headers_de())

    assert r.status_code == 201
    assert r.json()["nombre"] == "Mi app"
    assert r.json()["client_id"]
    assert r.json()["client_secret"]


def test_el_secret_no_se_guarda_en_texto_plano():
    from app.database import obtener_conexion

    r = client.post(URL, json={"nombre": "Mi app"}, headers=headers_de())

    with obtener_conexion() as conn:
        guardado = conn.execute(
            "SELECT hash_secret FROM aplicacion WHERE client_id = %s", (r.json()["client_id"],)
        ).fetchone()[0]
    assert guardado != r.json()["client_secret"]


def test_crear_sin_nombre_devuelve_400():
    r = client.post(URL, json={"nombre": "   "}, headers=headers_de())

    assert r.status_code == 400


def test_nombre_repetido_en_la_misma_organizacion_devuelve_409():
    headers = headers_de()
    client.post(URL, json={"nombre": "Mi app"}, headers=headers)
    r = client.post(URL, json={"nombre": "MI APP"}, headers=headers)

    assert r.status_code == 409


def test_listar_devuelve_solo_las_aplicaciones_de_mi_organizacion():
    headers = headers_de()
    otros = headers_de(OTRO_ADMIN)
    client.post(URL, json={"nombre": "Mía"}, headers=headers)
    client.post(URL, json={"nombre": "Ajena"}, headers=otros)

    r = client.get(URL, headers=headers)

    assert [a["nombre"] for a in r.json()] == ["Mía"]
    assert "client_secret" not in r.json()[0]


def test_regenerar_secret_devuelve_uno_nuevo():
    headers = headers_de()
    creada = client.post(URL, json={"nombre": "Mi app"}, headers=headers).json()

    r = client.post(f"{URL}{creada['client_id']}/regenerar-secret", headers=headers)

    assert r.status_code == 200
    assert r.json()["client_id"] == creada["client_id"]
    assert r.json()["client_secret"] != creada["client_secret"]


def test_regenerar_secret_de_una_aplicacion_ajena_devuelve_404():
    headers = headers_de()
    otros = headers_de(OTRO_ADMIN)
    ajena = client.post(URL, json={"nombre": "Ajena"}, headers=otros).json()

    r = client.post(f"{URL}{ajena['client_id']}/regenerar-secret", headers=headers)

    assert r.status_code == 404


def test_regenerar_secret_con_client_id_invalido_devuelve_422():
    r = client.post(f"{URL}no-es-un-uuid/regenerar-secret", headers=headers_de())

    assert r.status_code == 422
