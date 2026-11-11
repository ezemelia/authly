from tests.conftest import ADMIN, CODIGO, DOMINIO_TEST, client, emails_enviados, registrar_admin

URL = "/recovery/"
NUEVA = "Nueva-clave-1"
GENERICO = "Si el correo corresponde a una cuenta, le enviamos un código."


def _pedir(email=ADMIN["email"]):
    return client.post(URL + "codigo", json={"email": email})


def _confirmar(codigo=CODIGO, password=NUEVA, email=ADMIN["email"]):
    return client.post(URL + "confirmar", json={"email": email, "codigo": codigo, "password": password})


def _login(password):
    return client.post("/login", json={"email": ADMIN["email"], "password": password})


def test_pedir_codigo_responde_lo_mismo_exista_o_no_la_cuenta():
    registrar_admin()
    emails_enviados.clear()

    existente = _pedir()
    inexistente = _pedir(f"nadie{DOMINIO_TEST}")
    mal_formato = _pedir("esto-no-es-un-email")

    assert existente.status_code == inexistente.status_code == mal_formato.status_code == 200
    assert existente.json() == inexistente.json() == mal_formato.json() == {"detail": GENERICO}


def test_solo_se_envia_el_codigo_si_la_cuenta_existe():
    registrar_admin()
    emails_enviados.clear()

    _pedir(f"nadie{DOMINIO_TEST}")
    assert emails_enviados == []
    _pedir()
    assert emails_enviados == [(ADMIN["email"], CODIGO, "recuperacion")]


def test_pedir_codigo_acepta_el_email_con_mayusculas():
    registrar_admin()
    emails_enviados.clear()

    _pedir(f" ANA{DOMINIO_TEST} ")

    assert len(emails_enviados) == 1


def test_el_limite_de_codigos_responde_igual_y_no_envia_mas():
    registrar_admin()
    emails_enviados.clear()

    respuestas = [_pedir() for _ in range(4)]

    assert all(r.json() == {"detail": GENERICO} for r in respuestas)
    assert len(emails_enviados) == 3  # el cuarto no se envía y no se avisa


def test_recuperar_cambia_la_contrasena():
    registrar_admin()
    _pedir()

    r = _confirmar()

    assert r.status_code == 200
    assert _login(NUEVA).status_code == 200
    assert _login(ADMIN["password"]).status_code == 401  # la anterior deja de servir


def test_el_codigo_usado_no_sirve_de_nuevo():
    registrar_admin()
    _pedir()
    _confirmar()

    r = _confirmar(password="Otra-clave-22")

    assert r.status_code == 400
    assert r.json()["campo"] == "codigo"


def test_codigo_incorrecto_devuelve_un_mensaje_unico():
    registrar_admin()
    _pedir()

    r = _confirmar(codigo="000000")

    assert r.status_code == 400
    assert r.json()["campo"] == "codigo"
    assert r.json()["detail"] == "Código inválido o vencido."


def test_cinco_codigos_incorrectos_invalidan_el_codigo():
    registrar_admin()
    _pedir()
    for _ in range(5):
        _confirmar(codigo="000000")

    r = _confirmar()  # ni el correcto sirve ya

    assert r.status_code == 400
    assert r.json()["detail"] == "Código inválido o vencido."
    assert _login(ADMIN["password"]).status_code == 200


def test_sin_haber_pedido_codigo_da_el_mismo_error():
    registrar_admin()

    assert _confirmar().json()["detail"] == "Código inválido o vencido."


def test_email_inexistente_da_el_mismo_error_que_codigo_incorrecto():
    r = _confirmar(email=f"nadie{DOMINIO_TEST}")

    assert r.status_code == 400
    assert r.json()["detail"] == "Código inválido o vencido."


def test_contrasena_debil_con_codigo_valido_no_gasta_el_codigo():
    registrar_admin()
    _pedir()

    debil = _confirmar(password="abc")
    ok = _confirmar()  # el mismo código sigue valiendo

    assert debil.status_code == 400
    assert debil.json()["campo"] == "pass"
    assert ok.status_code == 200


def test_contrasena_igual_a_la_actual_se_rechaza_sin_gastar_el_codigo():
    registrar_admin()
    _pedir()

    igual = _confirmar(password=ADMIN["password"])
    ok = _confirmar()

    assert igual.status_code == 400
    assert igual.json()["campo"] == "pass"
    assert ok.status_code == 200


def test_los_errores_de_contrasena_no_consumen_intentos():
    registrar_admin()
    _pedir()
    for _ in range(6):
        _confirmar(password="abc")

    assert _confirmar().status_code == 200
