import pytest
from app.utils.validators import normalizar_email, validar_password


# ---------- normalizar_email (AURN-02) ----------

def test_normalizar_email_pasa_a_minusculas():
    # assert = "afirmo que esto es verdad": si la función no devuelve el email en minúsculas, el test falla
    assert normalizar_email("Valen@Mail.COM") == "valen@mail.com"


def test_normalizar_email_quita_espacios_de_los_bordes():
    # afirma que los espacios de los bordes desaparecen; si quedaran, el test falla
    assert normalizar_email("  valen@mail.com  ") == "valen@mail.com"


# ---------- validar_password (AURN-01) ----------

def test_password_valida():
    # No debe lanzar ninguna excepción
    validar_password("Abcdefgh1!")


def test_password_corta():
    with pytest.raises(ValueError):
        validar_password("Abc1!")


def test_password_sin_mayuscula():
    with pytest.raises(ValueError):
        validar_password("abcdefgh1!")


def test_password_sin_minuscula():
    with pytest.raises(ValueError):
        validar_password("ABCDEFGH1!")


def test_password_sin_numero():
    with pytest.raises(ValueError):
        validar_password("Abcdefghi!")


def test_password_sin_simbolo():
    with pytest.raises(ValueError):
        validar_password("Abcdefghi1")


# ---------- CU-01 extensión 2a: informar cada error ----------

def test_password_informa_todos_los_errores_juntos():
    # "abc" incumple varias reglas a la vez: largo, mayúscula, número y símbolo
    with pytest.raises(ValueError) as error:
        validar_password("abc")

    mensaje = str(error.value).lower()
    # cada assert afirma que el mensaje de error incluye esa palabra
    assert "10" in mensaje          # menciona el largo mínimo
    assert "mayúscula" in mensaje
    assert "número" in mensaje
    assert "símbolo" in mensaje