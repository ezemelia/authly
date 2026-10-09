import re

LARGO_MINIMO = 10


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def validar_password(password: str) -> None:
    """Lanza ValueError informando todas las reglas incumplidas juntas."""
    errores = []

    if len(password) < LARGO_MINIMO:
        errores.append(f"debe tener al menos {LARGO_MINIMO} caracteres")
    if not re.search(r"[A-ZÁÉÍÓÚÑ]", password):
        errores.append("debe incluir una mayúscula")
    if not re.search(r"[a-záéíóúñ]", password):
        errores.append("debe incluir una minúscula")
    if not re.search(r"\d", password):
        errores.append("debe incluir un número")
    if not re.search(r"[^\w\s]|_", password):
        errores.append("debe incluir un símbolo")

    if errores:
        raise ValueError("La contraseña " + "; ".join(errores))
