from app.database import obtener_conexion
from tests.conftest import CERO, OTRO_ADMIN, client, crear_app, crear_rol, headers_de, insertar_usuario, DOMINIO_TEST


def _url(client_id, rol_id=""):
    return f"/platform/applications/{client_id}/roles/{rol_id}"


def _app_con_headers():
    headers = headers_de()
    return headers, crear_app(headers)["client_id"]


def test_sin_token_devuelve_401():
    assert client.get(_url(CERO)).status_code == 401


def test_crear_rol_normaliza_y_devuelve_el_rol():
    headers, cid = _app_con_headers()

    r = client.post(
        _url(cid),
        json={"nombre": " Lector ", "descripcion": " Solo lectura ", "permisos": [{"recurso": " Documentos ", "accion": "LEER"}]},
        headers=headers,
    )

    assert r.status_code == 201
    rol = r.json()["rol"]
    assert rol["nombre"] == "Lector"
    assert rol["descripcion"] == "Solo lectura"
    assert rol["permisos"] == [{"recurso": "documentos", "accion": "leer"}]
    assert rol["por_defecto"] is False
    assert r.json()["rol_por_defecto_anterior"] is None


def test_crear_rol_sin_permisos_es_valido():
    headers, cid = _app_con_headers()

    r = client.post(_url(cid), json={"nombre": "Invitado"}, headers=headers)

    assert r.status_code == 201
    assert r.json()["rol"]["permisos"] == []


def test_nombre_repetido_sin_distinguir_mayusculas_devuelve_409():
    headers, cid = _app_con_headers()
    crear_rol(headers, cid, "Lector")

    r = client.post(_url(cid), json={"nombre": "LECTOR"}, headers=headers)

    assert r.status_code == 409
    assert r.json()["campo"] == "nombre"


def test_el_mismo_nombre_se_puede_usar_en_otra_aplicacion():
    headers, cid = _app_con_headers()
    otra = crear_app(headers, "Otra app")["client_id"]
    crear_rol(headers, cid, "Lector")

    assert client.post(_url(otra), json={"nombre": "Lector"}, headers=headers).status_code == 201


def test_permisos_invalidos_devuelven_400_en_el_campo_permisos():
    headers, cid = _app_con_headers()
    repetido = [{"recurso": "a", "accion": "b"}, {"recurso": "A", "accion": " B "}]
    vacio = [{"recurso": "  ", "accion": "b"}]

    for permisos in (repetido, vacio):
        r = client.post(_url(cid), json={"nombre": "X", "permisos": permisos}, headers=headers)
        assert r.status_code == 400
        assert r.json()["campo"] == "permisos"


def test_nombre_vacio_devuelve_400_y_nombre_demasiado_largo_422():
    headers, cid = _app_con_headers()

    vacio = client.post(_url(cid), json={"nombre": "   "}, headers=headers)
    largo = client.post(_url(cid), json={"nombre": "x" * 101}, headers=headers)

    assert vacio.status_code == 400 and vacio.json()["campo"] == "nombre"
    assert largo.status_code == 422


def test_listar_ordena_en_español_sin_distinguir_tildes():
    headers, cid = _app_con_headers()
    for nombre in ("Lector", "Álvarez", "Administrador", "zeta"):
        crear_rol(headers, cid, nombre)

    nombres = [r["nombre"] for r in client.get(_url(cid), headers=headers).json()["roles"]]

    assert nombres == ["Administrador", "Álvarez", "Lector", "zeta"]


def test_listar_incluye_permisos_y_cantidad_de_usuarios():
    headers, cid = _app_con_headers()
    rol = crear_rol(headers, cid, "Lector", permisos=[{"recurso": "docs", "accion": "leer"}])
    insertar_usuario(cid, "Ana", "Paz", f"ana{DOMINIO_TEST}", [rol["id"]])

    listado = client.get(_url(cid), headers=headers).json()["roles"]

    assert listado[0]["cantidad_usuarios"] == 1
    assert listado[0]["permisos"] == [{"recurso": "docs", "accion": "leer"}]


def test_marcar_rol_por_defecto_desmarca_al_anterior_y_lo_informa():
    headers, cid = _app_con_headers()
    crear_rol(headers, cid, "Lector", por_defecto=True)

    r = client.post(_url(cid), json={"nombre": "Invitado", "por_defecto": True}, headers=headers)

    assert r.json()["rol_por_defecto_anterior"] == "Lector"
    por_defecto = [x["nombre"] for x in client.get(_url(cid), headers=headers).json()["roles"] if x["por_defecto"]]
    assert por_defecto == ["Invitado"]  # solo uno por aplicación


def test_editar_rol_cambia_nombre_y_reemplaza_los_permisos():
    headers, cid = _app_con_headers()
    rol = crear_rol(headers, cid, "Lector", permisos=[{"recurso": "docs", "accion": "leer"}])

    r = client.put(
        _url(cid, rol["id"]),
        json={"nombre": "Editor", "permisos": [{"recurso": "docs", "accion": "editar"}]},
        headers=headers,
    )

    assert r.status_code == 200
    assert r.json()["rol"]["nombre"] == "Editor"
    assert r.json()["rol"]["permisos"] == [{"recurso": "docs", "accion": "editar"}]


def test_editar_rol_conservando_su_propio_nombre_no_da_conflicto():
    headers, cid = _app_con_headers()
    rol = crear_rol(headers, cid, "Lector")

    assert client.put(_url(cid, rol["id"]), json={"nombre": "lector"}, headers=headers).status_code == 200


def test_editar_a_un_nombre_de_otro_rol_devuelve_409():
    headers, cid = _app_con_headers()
    crear_rol(headers, cid, "Lector")
    otro = crear_rol(headers, cid, "Editor")

    r = client.put(_url(cid, otro["id"]), json={"nombre": "lector"}, headers=headers)

    assert r.status_code == 409
    assert r.json()["campo"] == "nombre"


def test_quitar_la_marca_por_defecto_deja_la_aplicacion_sin_rol_por_defecto():
    headers, cid = _app_con_headers()
    rol = crear_rol(headers, cid, "Lector", por_defecto=True)

    client.put(_url(cid, rol["id"]), json={"nombre": "Lector", "por_defecto": False}, headers=headers)

    assert not any(x["por_defecto"] for x in client.get(_url(cid), headers=headers).json()["roles"])


def test_editar_rol_inexistente_devuelve_404():
    headers, cid = _app_con_headers()

    r = client.put(_url(cid, CERO), json={"nombre": "X"}, headers=headers)

    assert r.status_code == 404
    assert r.json()["motivo"] == "rol-inexistente"


def test_eliminar_rol_sin_usuarios_borra_el_rol_y_sus_permisos():
    headers, cid = _app_con_headers()
    rol = crear_rol(headers, cid, "Lector", permisos=[{"recurso": "docs", "accion": "leer"}])

    r = client.delete(_url(cid, rol["id"]), headers=headers)

    assert r.status_code == 200
    assert client.get(_url(cid), headers=headers).json()["roles"] == []
    with obtener_conexion() as conn:
        assert conn.execute("SELECT COUNT(*) FROM permiso WHERE rol_id = %s", (rol["id"],)).fetchone()[0] == 0


def test_eliminar_rol_con_usuarios_devuelve_409_y_no_borra_nada():
    headers, cid = _app_con_headers()
    rol = crear_rol(headers, cid, "Lector")
    insertar_usuario(cid, "Ana", "Paz", f"ana{DOMINIO_TEST}", [rol["id"]])

    r = client.delete(_url(cid, rol["id"]), headers=headers)

    assert r.status_code == 409
    assert r.json()["motivo"] == "tiene-usuarios"
    assert r.json()["cantidad_usuarios"] == 1
    assert len(client.get(_url(cid), headers=headers).json()["roles"]) == 1


def test_eliminar_rol_inexistente_devuelve_404():
    headers, cid = _app_con_headers()

    assert client.delete(_url(cid, CERO), headers=headers).status_code == 404


def test_no_se_pueden_gestionar_roles_de_otra_organizacion():
    headers, cid = _app_con_headers()
    rol = crear_rol(headers, cid, "Lector")
    ajeno = headers_de(OTRO_ADMIN)

    assert client.get(_url(cid), headers=ajeno).status_code == 404
    assert client.post(_url(cid), json={"nombre": "Hack"}, headers=ajeno).status_code == 404
    assert client.put(_url(cid, rol["id"]), json={"nombre": "Hack"}, headers=ajeno).status_code == 404
    assert client.delete(_url(cid, rol["id"]), headers=ajeno).status_code == 404
    assert len(client.get(_url(cid), headers=headers).json()["roles"]) == 1  # nada cambió
