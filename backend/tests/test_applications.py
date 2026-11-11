from tests.conftest import ADMIN, CERO, DOMINIO_TEST, PREFIJO_CUIT, client, crear_app, headers_de

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

    aplicaciones = r.json()["aplicaciones"]
    assert [a["nombre"] for a in aplicaciones] == ["Mía"]
    assert "client_secret" not in aplicaciones[0]
    assert "hash_secret" not in aplicaciones[0]


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


def test_listar_pagina_y_ordena_por_nombre_e_informa_totales():
    headers = headers_de()
    for nombre in ("Cuarta", "Primera", "Tercera", "Segunda"):
        client.post(URL, json={"nombre": nombre}, headers=headers)

    pagina1 = client.get(URL + "?pagina=1&tamanio=3", headers=headers).json()
    pagina2 = client.get(URL + "?pagina=2&tamanio=3", headers=headers).json()

    assert [a["nombre"] for a in pagina1["aplicaciones"]] == ["Cuarta", "Primera", "Segunda"]
    assert [a["nombre"] for a in pagina2["aplicaciones"]] == ["Tercera"]
    assert pagina1["total_apps"] == 4
    assert pagina1["aplicaciones"][0]["cantidad_usuarios"] == 0


def test_obtener_una_aplicacion():
    headers = headers_de()
    app = crear_app(headers, "Mi app")

    r = client.get(f"{URL}{app['client_id']}", headers=headers)

    assert r.status_code == 200
    assert r.json()["nombre"] == "Mi app"
    assert r.json()["cantidad_usuarios"] == 0


def test_obtener_una_aplicacion_ajena_o_inexistente_devuelve_404():
    headers = headers_de()
    ajena = crear_app(headers_de(OTRO_ADMIN), "Ajena")

    assert client.get(f"{URL}{ajena['client_id']}", headers=headers).status_code == 404
    assert client.get(f"{URL}{CERO}", headers=headers).status_code == 404


def test_editar_aplicacion():
    headers = headers_de()
    app = crear_app(headers, "Vieja")

    r = client.put(f"{URL}{app['client_id']}", json={"nombre": " Nueva ", "descripcion": "otra"}, headers=headers)

    assert r.status_code == 200
    assert (r.json()["nombre"], r.json()["descripcion"]) == ("Nueva", "otra")


def test_editar_aplicacion_con_el_nombre_de_otra_devuelve_409():
    headers = headers_de()
    crear_app(headers, "Una")
    otra = crear_app(headers, "Otra")

    r = client.put(f"{URL}{otra['client_id']}", json={"nombre": "una"}, headers=headers)

    assert r.status_code == 409
    assert r.json()["campo"] == "nombre"


def test_editar_aplicacion_ajena_devuelve_404():
    headers = headers_de()
    ajena = crear_app(headers_de(OTRO_ADMIN), "Ajena")

    r = client.put(f"{URL}{ajena['client_id']}", json={"nombre": "Hack"}, headers=headers)

    assert r.status_code == 404


def test_eliminar_aplicacion_sin_usuarios_devuelve_204_y_la_borra():
    headers = headers_de()
    app = crear_app(headers, "Mi app")

    r = client.delete(f"{URL}{app['client_id']}", headers=headers)

    assert r.status_code == 204
    assert client.get(f"{URL}{app['client_id']}", headers=headers).status_code == 404


def test_eliminar_aplicacion_ajena_devuelve_404_y_no_la_borra():
    headers = headers_de()
    ajeno = headers_de(OTRO_ADMIN)
    ajena = crear_app(ajeno, "Ajena")

    assert client.delete(f"{URL}{ajena['client_id']}", headers=headers).status_code == 404
    assert client.get(f"{URL}{ajena['client_id']}", headers=ajeno).status_code == 200
