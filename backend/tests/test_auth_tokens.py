from datetime import datetime, timezone

import jwt
import pytest

from app import config
from app.services.auth import crear_token, leer_token

# Estos tests no usan la base de datos ni el servidor: prueban solo la generación del token.
ID = "d681b122-fb20-434f-9dd6-734bf0fd79f1"  # los ids son uuid
ADMIN = {"sub": ID, "type": "admin", "org_id": "f4932f4d-9333-4cbe-ab16-524cc2bb7636"}
USUARIO_APP = {**ADMIN, "type": "user", "app_id": "9d5b8eac-fdeb-492f-81b2-2e02fcc4ee12"}


def test_crear_token_devuelve_un_texto_con_tres_partes():
    token = crear_token(ADMIN)

    # un JWT tiene la forma "cabecera.contenido.firma"
    assert isinstance(token, str)
    assert len(token.split(".")) == 3


def test_el_token_esta_firmado_con_rs256():
    token = crear_token(ADMIN)

    # la cabecera se puede leer sin verificar la firma
    assert jwt.get_unverified_header(token)["alg"] == "RS256"


def test_el_token_guarda_el_id_y_el_tipo():
    payload = jwt.decode(crear_token(ADMIN), config.JWT_PUBLIC_KEY, algorithms=["RS256"])

    assert payload["sub"] == ID
    assert payload["type"] == "admin"


def test_el_sub_se_guarda_siempre_como_texto():
    payload = jwt.decode(crear_token({**ADMIN, "sub": 42}), config.JWT_PUBLIC_KEY, algorithms=["RS256"])

    assert payload["sub"] == "42"


def test_el_token_solo_contiene_los_datos_pedidos_mas_iat_y_exp():
    token = crear_token({**USUARIO_APP, "password_hash": "no-deberia-estar"})
    payload = jwt.decode(token, config.JWT_PUBLIC_KEY, algorithms=["RS256"])

    # crear_token no filtra: lo que se le pasa va al token, así que el llamador no debe pasar datos sensibles
    assert set(payload) == {"sub", "type", "org_id", "app_id", "password_hash", "iat", "exp"}
    assert set(crear_token_payload(USUARIO_APP)) == {"sub", "type", "org_id", "app_id", "iat", "exp"}


def crear_token_payload(claims):
    return jwt.decode(crear_token(claims), config.JWT_PUBLIC_KEY, algorithms=["RS256"])


def test_el_token_vence_en_el_tiempo_configurado():
    antes = datetime.now(timezone.utc)
    payload = crear_token_payload(ADMIN)

    vence = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    minutos = (vence - antes).total_seconds() / 60
    # tolerancia de 1 minuto por el tiempo que tarda el test en correr
    assert config.JWT_EXPIRA_MINUTOS - 1 <= minutos <= config.JWT_EXPIRA_MINUTOS


def test_crear_token_sin_sub_falla():
    with pytest.raises(KeyError):
        crear_token({"type": "admin"})


def test_leer_token_devuelve_el_payload_completo():
    payload = leer_token(crear_token(USUARIO_APP))

    assert payload["sub"] == ID
    assert payload["type"] == "user"
    assert payload["org_id"] == USUARIO_APP["org_id"]
    assert payload["app_id"] == USUARIO_APP["app_id"]


def test_leer_token_rechaza_un_token_alterado():
    token = crear_token(ADMIN)
    # se cambia el último carácter de la firma: ya no coincide con el contenido
    alterado = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(jwt.InvalidTokenError):
        leer_token(alterado)


def test_leer_token_rechaza_un_token_vencido():
    vencido = jwt.encode({"sub": ID, "exp": 1}, config.JWT_PRIVATE_KEY, algorithm="RS256")

    with pytest.raises(jwt.ExpiredSignatureError):
        leer_token(vencido)
