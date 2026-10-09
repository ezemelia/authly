import os

import psycopg
from dotenv import load_dotenv

load_dotenv()  # carga el .env para que os.environ tenga los datos de la base

def obtener_conexion():
    try:
        conexion = psycopg.connect(
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT"),             # el puerto donde escucha PostgreSQL
            dbname=os.environ.get("DB_NAME"),           # el nombre de la base de datos
            user=os.environ.get("DB_USER"),             # el usuario de PostgreSQL
            password=os.environ.get("DB_PASSWORD"),     # la contraseña de ese usuario
        )
        return conexion
    except psycopg.OperationalError as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None