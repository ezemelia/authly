from app.database import obtener_conexion
from tests.conftest import (
    CERO, DOMINIO_TEST, OTRO_ADMIN, client, crear_app, crear_rol, headers_de, insertar_usuario,
)


def _url(client_id, usuario_id=""):
    return f"/platform/applications/{client_id}/users/{usuario_id}"


def _app_con_rol():
    headers = headers_de()
    cid = crear_app(headers)["client_id"]
    return headers, cid, crear_rol(headers, cid, "Lector")


def _usuario(cid, rol, nombre="Ana", apellido="Paz", email=f"ana{DOMINIO_TEST}"):
    return insertar_usuario(cid, nombre, apellido, email, [rol["id"]])


def test_sin_token_devuelve_401():
    assert client.get(_url(CERO)).status_code == 401


# ---------- listar ----------

def test_listar_devuelve_nombre_apellido_email_y_roles():
    headers, cid, rol = _app_con_rol()
    _usuario(cid, rol)

    r = client.get(_url(cid), headers=headers)

    assert r.status_code == 200
    assert r.json()["total"] == 1
    usuario = r.json()["usuarios"][0]
    assert (usuario["nombre"], usuario["apellido"], usuario["email"]) == ("Ana", "Paz", f"ana{DOMINIO_TEST}")
    assert usuario["roles"] == [{"id": rol["id"], "nombre": "Lector"}]
    assert "hash_contrasena" not in usuario


def test_listar_ordena_por_apellido_en_español_y_pagina():
    headers, cid, rol = _app_con_rol()
    for nombre, apellido in (("Sofía", "Benítez"), ("Zoe", "Aguirre"), ("Marta", "Álvarez"), ("Luis", "Ferreyra")):
        _usuario(cid, rol, nombre, apellido, f"{nombre.lower().replace('í', 'i')}{DOMINIO_TEST}")

    pagina1 = client.get(_url(cid) + "?pagina=1&tamanio=3", headers=headers).json()
    pagina2 = client.get(_url(cid) + "?pagina=2&tamanio=3", headers=headers).json()

    # "Álvarez" va entre "Aguirre" y "Benítez"
    assert [u["apellido"] for u in pagina1["usuarios"]] == ["Aguirre", "Álvarez", "Benítez"]
    assert [u["apellido"] for u in pagina2["usuarios"]] == ["Ferreyra"]
    assert pagina1["total"] == pagina2["total"] == 4


def test_listar_con_paginacion_invalida_devuelve_422():
    headers, cid, _ = _app_con_rol()

    assert client.get(_url(cid) + "?pagina=0", headers=headers).status_code == 422
    assert client.get(_url(cid) + "?tamanio=101", headers=headers).status_code == 422


def test_listar_solo_muestra_los_usuarios_de_esa_aplicacion():
    headers, cid, rol = _app_con_rol()
    otra = crear_app(headers, "Otra app")["client_id"]
    _usuario(cid, rol)

    assert client.get(_url(otra), headers=headers).json()["total"] == 0


# ---------- editar ----------

def test_editar_cambia_nombre_apellido_y_roles_en_una_operacion():
    headers, cid, rol = _app_con_rol()
    editor = crear_rol(headers, cid, "Editor")
    usuario_id = _usuario(cid, rol)

    r = client.put(
        _url(cid, usuario_id),
        json={"nombre": " Anita ", "apellido": "Gómez", "roles": [editor["id"], rol["id"], editor["id"]]},
        headers=headers,
    )

    assert r.status_code == 200
    assert (r.json()["nombre"], r.json()["apellido"]) == ("Anita", "Gómez")
    assert sorted(x["nombre"] for x in r.json()["roles"]) == ["Editor", "Lector"]  # sin repetidos


def test_editar_no_modifica_el_email():
    headers, cid, rol = _app_con_rol()
    usuario_id = _usuario(cid, rol)

    r = client.put(
        _url(cid, usuario_id),
        json={"nombre": "A", "apellido": "B", "roles": [rol["id"]], "email": "otro@x.com"},
        headers=headers,
    )

    assert r.json()["email"] == f"ana{DOMINIO_TEST}"


def test_editar_sin_roles_devuelve_400_en_el_campo_roles():
    headers, cid, rol = _app_con_rol()
    usuario_id = _usuario(cid, rol)

    r = client.put(_url(cid, usuario_id), json={"nombre": "A", "apellido": "B", "roles": []}, headers=headers)

    assert r.status_code == 400
    assert r.json()["campo"] == "roles"


def test_editar_con_nombre_o_apellido_vacio_devuelve_400():
    headers, cid, rol = _app_con_rol()
    usuario_id = _usuario(cid, rol)

    sin_nombre = client.put(_url(cid, usuario_id), json={"nombre": " ", "apellido": "B", "roles": [rol["id"]]}, headers=headers)
    sin_apellido = client.put(_url(cid, usuario_id), json={"nombre": "A", "apellido": "", "roles": [rol["id"]]}, headers=headers)

    assert (sin_nombre.status_code, sin_nombre.json()["campo"]) == (400, "nombre")
    assert (sin_apellido.status_code, sin_apellido.json()["campo"]) == (400, "apellido")


def test_editar_con_un_rol_inexistente_falla_y_no_cambia_nada():
    headers, cid, rol = _app_con_rol()
    usuario_id = _usuario(cid, rol)

    r = client.put(_url(cid, usuario_id), json={"nombre": "Nuevo", "apellido": "Nuevo", "roles": [rol["id"], CERO]}, headers=headers)

    assert r.status_code == 404
    assert r.json()["motivo"] == "rol-inexistente"
    assert r.json()["rol_id"] == CERO
    sigue = client.get(_url(cid), headers=headers).json()["usuarios"][0]
    assert (sigue["nombre"], sigue["apellido"]) == ("Ana", "Paz")  # atómico: ni el nombre cambió
    assert [x["nombre"] for x in sigue["roles"]] == ["Lector"]


def test_editar_con_un_rol_de_otra_aplicacion_falla():
    headers, cid, rol = _app_con_rol()
    otra = crear_app(headers, "Otra app")["client_id"]
    rol_ajeno = crear_rol(headers, otra, "Ajeno")
    usuario_id = _usuario(cid, rol)

    r = client.put(_url(cid, usuario_id), json={"nombre": "A", "apellido": "B", "roles": [rol_ajeno["id"]]}, headers=headers)

    assert r.status_code == 404
    assert r.json()["motivo"] == "rol-inexistente"


def test_editar_usuario_inexistente_devuelve_404():
    headers, cid, rol = _app_con_rol()

    r = client.put(_url(cid, CERO), json={"nombre": "A", "apellido": "B", "roles": [rol["id"]]}, headers=headers)

    assert r.status_code == 404
    assert r.json()["motivo"] == "usuario-inexistente"


# ---------- eliminar ----------

def test_eliminar_borra_al_usuario_y_sus_asignaciones():
    headers, cid, rol = _app_con_rol()
    usuario_id = _usuario(cid, rol)

    r = client.delete(_url(cid, usuario_id), headers=headers)

    assert r.status_code == 200
    assert r.json()["email"] == f"ana{DOMINIO_TEST}"
    assert client.get(_url(cid), headers=headers).json()["total"] == 0
    with obtener_conexion() as conn:
        assert conn.execute("SELECT COUNT(*) FROM usuario_rol WHERE usuario_id = %s", (usuario_id,)).fetchone()[0] == 0


def test_eliminar_dos_veces_devuelve_404_la_segunda():
    headers, cid, rol = _app_con_rol()
    usuario_id = _usuario(cid, rol)
    client.delete(_url(cid, usuario_id), headers=headers)

    r = client.delete(_url(cid, usuario_id), headers=headers)

    assert r.status_code == 404
    assert r.json()["motivo"] == "usuario-inexistente"


def test_eliminar_el_ultimo_usuario_de_un_rol_permite_borrar_el_rol():
    headers, cid, rol = _app_con_rol()
    usuario_id = _usuario(cid, rol)
    client.delete(_url(cid, usuario_id), headers=headers)

    assert client.delete(f"/platform/applications/{cid}/roles/{rol['id']}", headers=headers).status_code == 200


# ---------- aislamiento ----------

def test_no_se_pueden_gestionar_usuarios_de_otra_organizacion():
    headers, cid, rol = _app_con_rol()
    usuario_id = _usuario(cid, rol)
    ajeno = headers_de(OTRO_ADMIN)
    cuerpo = {"nombre": "Hack", "apellido": "Hack", "roles": [rol["id"]]}

    assert client.get(_url(cid), headers=ajeno).status_code == 404
    assert client.put(_url(cid, usuario_id), json=cuerpo, headers=ajeno).status_code == 404
    assert client.delete(_url(cid, usuario_id), headers=ajeno).status_code == 404
    sigue = client.get(_url(cid), headers=headers).json()["usuarios"][0]
    assert sigue["nombre"] == "Ana"  # nada cambió
