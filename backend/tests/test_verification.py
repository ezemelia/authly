import pytest

from app.database import obtener_conexion
from app.services import verification
from app.services.verification import (
    CodigoIncorrecto, CodigoInexistente, CodigoVencido, ErrorEnvioCodigo, IntentosAgotados,
    LimiteCodigosExcedido, generar_codigo, validar_codigo,
)
from tests.conftest import ADMIN, CODIGO, DOMINIO_TEST, client, emails_enviados, headers_de

EMAIL = f"verif{DOMINIO_TEST}"


def _estados(email=EMAIL, tabla="codigo_administrador"):
    with obtener_conexion() as conn:
        return [
            f[0]
            for f in conn.execute(
                f"SELECT estado FROM {tabla} WHERE email = %s ORDER BY emitido_en", (email,)
            ).fetchall()
        ]


def test_generar_codigo_guarda_hash_y_envia_el_email():
    generar_codigo(EMAIL, "registro")

    assert emails_enviados == [(EMAIL, CODIGO, "registro")]
    with obtener_conexion() as conn:
        guardado = conn.execute(
            "SELECT hash_codigo FROM codigo_administrador WHERE email = %s", (EMAIL,)
        ).fetchone()[0]
    assert guardado != CODIGO
    assert len(guardado) == 64  # HMAC-SHA256 en hexadecimal


def test_el_hash_depende_de_la_clave_secreta(monkeypatch):
    monkeypatch.setenv("CODIGO_HMAC_KEY", "clave-uno")
    uno = verification._hash_codigo(EMAIL, CODIGO, "registro", None)
    monkeypatch.setenv("CODIGO_HMAC_KEY", "clave-dos")
    dos = verification._hash_codigo(EMAIL, CODIGO, "registro", None)

    assert uno != dos


def test_sin_clave_hmac_falla(monkeypatch):
    monkeypatch.delenv("CODIGO_HMAC_KEY")

    with pytest.raises(RuntimeError):
        generar_codigo(EMAIL, "registro")


def test_proposito_invalido_falla():
    with pytest.raises(ValueError):
        generar_codigo(EMAIL, "otro")


def test_maximo_tres_codigos_por_hora():
    for _ in range(3):
        generar_codigo(EMAIL, "registro")

    with pytest.raises(LimiteCodigosExcedido):
        generar_codigo(EMAIL, "registro")


def test_el_limite_es_por_proposito():
    for _ in range(3):
        generar_codigo(EMAIL, "registro")

    generar_codigo(EMAIL, "recuperacion")  # otro propósito: no se cuenta junto


def test_un_codigo_nuevo_reemplaza_al_pendiente():
    generar_codigo(EMAIL, "registro")
    generar_codigo(EMAIL, "registro")

    assert _estados() == ["reemplazado", "pendiente"]


def test_se_borran_los_codigos_de_mas_de_una_hora():
    generar_codigo(EMAIL, "registro")
    with obtener_conexion() as conn:
        conn.execute(
            "UPDATE codigo_administrador SET emitido_en = now() - interval '3 hours', "
            "vence_en = now() - interval '2 hours' WHERE email = %s",
            (EMAIL,),
        )
    generar_codigo(EMAIL, "registro")

    assert _estados() == ["pendiente"]


def test_si_falla_el_envio_lanza_error_y_el_codigo_queda_guardado(monkeypatch):
    def roto(*a):
        raise OSError("sin conexión")

    monkeypatch.setattr(verification, "_enviar_email", roto)

    with pytest.raises(ErrorEnvioCodigo):
        generar_codigo(EMAIL, "registro")
    assert _estados() == ["pendiente"]


def test_validar_codigo_correcto_lo_marca_usado():
    generar_codigo(EMAIL, "registro")

    validar_codigo(EMAIL, CODIGO, "registro")

    assert _estados() == ["usado"]


def test_validar_acepta_el_email_con_mayusculas_y_el_codigo_con_espacios():
    generar_codigo(EMAIL, "registro")

    validar_codigo(EMAIL.upper(), f" {CODIGO} ", "registro")


def test_un_codigo_usado_no_se_puede_reutilizar():
    generar_codigo(EMAIL, "registro")
    validar_codigo(EMAIL, CODIGO, "registro")

    with pytest.raises(CodigoInexistente):
        validar_codigo(EMAIL, CODIGO, "registro")


def test_validar_sin_haber_pedido_codigo():
    with pytest.raises(CodigoInexistente):
        validar_codigo(EMAIL, CODIGO, "registro")


def test_validar_con_otro_proposito_no_sirve():
    generar_codigo(EMAIL, "registro")

    with pytest.raises(CodigoInexistente):
        validar_codigo(EMAIL, CODIGO, "recuperacion")


def test_codigo_incorrecto_informa_los_intentos_restantes():
    generar_codigo(EMAIL, "registro")

    with pytest.raises(CodigoIncorrecto) as e:
        validar_codigo(EMAIL, "000000", "registro")
    assert e.value.intentos_restantes == 4


def test_cinco_intentos_fallidos_agotan_el_codigo():
    generar_codigo(EMAIL, "registro")
    for _ in range(4):
        with pytest.raises(CodigoIncorrecto):
            validar_codigo(EMAIL, "000000", "registro")
    with pytest.raises(IntentosAgotados):
        validar_codigo(EMAIL, "000000", "registro")

    # ni con el código correcto
    with pytest.raises(IntentosAgotados):
        validar_codigo(EMAIL, CODIGO, "registro")


def test_codigo_vencido():
    generar_codigo(EMAIL, "registro")
    with obtener_conexion() as conn:
        conn.execute(
            "UPDATE codigo_administrador SET emitido_en = now() - interval '20 minutes', "
            "vence_en = now() - interval '10 minutes' WHERE email = %s",
            (EMAIL,),
        )

    with pytest.raises(CodigoVencido):
        validar_codigo(EMAIL, CODIGO, "registro")


def test_con_conn_propia_el_usado_se_deshace_si_el_llamador_hace_rollback():
    generar_codigo(EMAIL, "registro")

    conn = obtener_conexion()
    validar_codigo(EMAIL, CODIGO, "registro", conn=conn)
    conn.rollback()
    conn.close()

    assert _estados() == ["pendiente"]


def test_con_conn_propia_el_intento_fallido_se_conserva_aunque_haya_rollback():
    generar_codigo(EMAIL, "registro")

    conn = obtener_conexion()
    with pytest.raises(CodigoIncorrecto):
        validar_codigo(EMAIL, "000000", "registro", conn=conn)
    conn.rollback()
    conn.close()

    with obtener_conexion() as c:
        intentos = c.execute("SELECT intentos FROM codigo_administrador WHERE email = %s", (EMAIL,)).fetchone()[0]
    assert intentos == 1


# ---------- códigos de usuarios de una aplicación (codigo_usuario) ----------

def _crear_aplicacion():
    headers = headers_de()
    return client.post("/platform/applications/", json={"nombre": "App verif"}, headers=headers).json()["client_id"]


def test_codigos_de_usuario_van_a_codigo_usuario_con_su_aplicacion():
    app_id = _crear_aplicacion()
    email = f"user{DOMINIO_TEST}"

    generar_codigo(email, "registro", app_id)
    validar_codigo(email, CODIGO, "registro", app_id)

    assert _estados(email, "codigo_usuario") == ["usado"]
    assert _estados(email, "codigo_administrador") == []


def test_un_codigo_de_una_aplicacion_no_sirve_en_otra():
    app_a = _crear_aplicacion()
    headers = headers_de()
    app_b = client.post("/platform/applications/", json={"nombre": "Otra app"}, headers=headers).json()["client_id"]
    email = f"user{DOMINIO_TEST}"

    generar_codigo(email, "registro", app_a)

    with pytest.raises(CodigoInexistente):
        validar_codigo(email, CODIGO, "registro", app_b)


def test_el_limite_por_hora_es_por_aplicacion():
    app_a = _crear_aplicacion()
    headers = headers_de()
    app_b = client.post("/platform/applications/", json={"nombre": "Otra app"}, headers=headers).json()["client_id"]
    email = f"user{DOMINIO_TEST}"
    for _ in range(3):
        generar_codigo(email, "registro", app_a)

    with pytest.raises(LimiteCodigosExcedido):
        generar_codigo(email, "registro", app_a)
    generar_codigo(email, "registro", app_b)  # otra aplicación: cuenta aparte
