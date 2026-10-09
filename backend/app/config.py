import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # lee el .env y lo carga como variables de entorno

BACKEND_DIR = Path(__file__).resolve().parent.parent  # carpeta backend/


def _leer_clave(variable: str) -> str:
    # las rutas del .env son relativas a backend/, así funciona desde cualquier carpeta
    return (BACKEND_DIR / os.environ[variable]).read_text()


JWT_ALGORITMO = "RS256"  # firma asimétrica: privada firma, pública verifica
JWT_PRIVATE_KEY = _leer_clave("JWT_PRIVATE_KEY_PATH")
JWT_PUBLIC_KEY = _leer_clave("JWT_PUBLIC_KEY_PATH")
JWT_EXPIRA_MINUTOS = 60
