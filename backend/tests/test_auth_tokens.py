from datetime import datetime, timezone

import jwt
import pytest

from app import config
from app.services.auth import crear_token, leer_token

# Estos tests no usan la base de datos ni el servidor: prueban solo la generación del token.
USUARIO = {"id": 42, "username": "ana", "email": "ana@mail.com"}


def test_crear_token_devuelve_un_texto_con_tres_partes():
    token = crear_token(USUARIO)

    # un JWT tiene la forma "cabecera.contenido.firma"
    assert isinstance(token, str)
    assert len(token.split(".")) == 3


def test_el_token_esta_firmado_con_rs256():
    token = crear_token(USUARIO)

    # la cabecera se puede leer sin verificar la firma
    assert jwt.get_unverified_header(token)["alg"] == "RS256"


def test_el_token_guarda_el_id_del_usuario():
    token = crear_token(USUARIO)

    payload = jwt.decode(token, config.JWT_PUBLIC_KEY, algorithms=["RS256"])
    assert payload["sub"] == "42"


def test_el_token_no_contiene_datos_sensibles():
    token = crear_token({**USUARIO, "password_hash": "$2b$12$secreto"})

    payload = jwt.decode(token, config.JWT_PUBLIC_KEY, algorithms=["RS256"])
    assert set(payload) == {"sub", "exp"}  # solo id y vencimiento


def test_el_token_vence_en_el_tiempo_configurado():
    antes = datetime.now(timezone.utc)
    token = crear_token(USUARIO)

    payload = jwt.decode(token, config.JWT_PUBLIC_KEY, algorithms=["RS256"])
    vence = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    minutos = (vence - antes).total_seconds() / 60
    # tolerancia de 1 minuto por el tiempo que tarda el test en correr
    assert config.JWT_EXPIRA_MINUTOS - 1 <= minutos <= config.JWT_EXPIRA_MINUTOS


def test_leer_token_devuelve_el_id_del_usuario():
    token = crear_token(USUARIO)

    assert leer_token(token) == 42


def test_leer_token_rechaza_un_token_alterado():
    token = crear_token(USUARIO)
    # se cambia el último carácter de la firma: ya no coincide con el contenido
    alterado = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(jwt.InvalidTokenError):
        leer_token(alterado)


def test_dos_tokens_del_mismo_usuario_se_pueden_leer_ambos():
    # cada login genera un token nuevo, pero los dos identifican al mismo usuario
    assert leer_token(crear_token(USUARIO)) == leer_token(crear_token(USUARIO)) == 42
