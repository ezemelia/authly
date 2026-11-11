import hashlib
import secrets

from app.database import obtener_conexion


class NombreAppDuplicado(Exception):
    pass 

class AplicacionConUsuarios(Exception):
    def __init__(self, cantidad: int):
        super().__init__(f"No se puede eliminar: la aplicación tiene {cantidad} usuario(s) asociado(s).")
        self.cantidad = cantidad


def _conectar():
    conexion = obtener_conexion()
    if conexion is None:
        raise RuntimeError("No se pudo conectar a la base de datos")
    return conexion


def _hash_secret(client_secret: str) -> str:
    # el secret es aleatorio y largo, así que alcanza con SHA-256 (es el formato que usa la base)
    return hashlib.sha256(client_secret.encode()).hexdigest()


def crear_aplicacion(nombre: str, descripcion: str, organizacion_id) -> dict:
    nombre = nombre.strip()
    descripcion = (descripcion or "").strip()
    client_secret = secrets.token_urlsafe(32)

    with _conectar() as conn:
        existe = conn.execute(
            "SELECT 1 FROM aplicacion WHERE organizacion_id = %s AND lower(nombre) = lower(%s)",
            (organizacion_id, nombre),
        ).fetchone()
        if existe:
            raise NombreAppDuplicado(f"Ya existe una aplicación con el nombre '{nombre}'.")
        fila = conn.execute(
            """
            INSERT INTO aplicacion (organizacion_id, nombre, descripcion, hash_secret)
            VALUES (%s, %s, %s, %s)
            RETURNING client_id
            """,
            (organizacion_id, nombre, descripcion, _hash_secret(client_secret)),
        ).fetchone()

    return {"nombre": nombre, "client_id": str(fila[0]), "client_secret": client_secret}


def listar_aplicaciones(organizacion_id, pagina: int = 1, tamanio: int = 10) -> dict:
    offset = (pagina - 1) * tamanio

    with _conectar() as conn:
        # Total de aplicaciones (para paginación)
        total_apps = conn.execute(
            "SELECT COUNT(*) FROM aplicacion WHERE organizacion_id = %s",
            (organizacion_id,),
        ).fetchone()[0]

        # Aplicaciones con conteo de usuarios, ordenadas por nombre
        filas = conn.execute(
            """
            SELECT a.client_id, a.nombre, a.descripcion, a.creado_en,
                COUNT(u.id) AS cantidad_usuarios
            FROM aplicacion a
            LEFT JOIN usuario u ON u.aplicacion_id = a.client_id
            WHERE a.organizacion_id = %s
            GROUP BY a.client_id, a.nombre, a.descripcion, a.creado_en
            ORDER BY a.nombre ASC
            LIMIT %s OFFSET %s
            """,
            (organizacion_id, tamanio, offset),
        ).fetchall()

        # Total de usuarios de la organización
        total_usuarios = conn.execute(
            """
            SELECT COUNT(*) FROM usuario u
            JOIN aplicacion a ON u.aplicacion_id = a.client_id
            WHERE a.organizacion_id = %s
            """,
            (organizacion_id,),
        ).fetchone()[0]

    aplicaciones = [
        {
            "client_id": str(f[0]),
            "nombre": f[1],
            "descripcion": f[2],
            "creado_en": f[3].isoformat(),
            "cantidad_usuarios": f[4],
        }
        for f in filas
    ]

    return {
        "aplicaciones": aplicaciones,
        "pagina": pagina,
        "tamanio": tamanio,
        "total_apps": total_apps,
        "total_usuarios_organizacion": total_usuarios,
    }

def obtener_aplicacion(client_id, organizacion_id) -> dict:
    with _conectar() as conn:
        fila = conn.execute(
            """
            SELECT a.client_id, a.nombre, a.descripcion, a.creado_en,
                   COUNT(u.id) AS cantidad_usuarios
            FROM aplicacion a
            LEFT JOIN usuario u ON u.aplicacion_id = a.client_id
            WHERE a.client_id = %s AND a.organizacion_id = %s
            GROUP BY a.client_id, a.nombre, a.descripcion, a.creado_en
            """,
            (client_id, organizacion_id),
        ).fetchone()

    if fila is None:
        raise ValueError("Aplicación no encontrada.")

    return {
        "client_id": str(fila[0]),
        "nombre": fila[1],
        "descripcion": fila[2],
        "creado_en": fila[3].isoformat(),
        "cantidad_usuarios": fila[4],
    }

def regenerar_secret(client_id, organizacion_id) -> dict:
    client_secret = secrets.token_urlsafe(32)

    with _conectar() as conn:
        fila = conn.execute(
            """
            UPDATE aplicacion
            SET hash_secret = %s
            WHERE client_id = %s AND organizacion_id = %s
            RETURNING client_id
            """,
            (_hash_secret(client_secret), client_id, organizacion_id),
        ).fetchone()

    if fila is None:
        raise ValueError("Aplicación no encontrada.")

    return {"client_id": str(fila[0]), "client_secret": client_secret}

def editar_aplicacion(client_id, nombre: str, descripcion: str, organizacion_id) -> dict:
    nombre = nombre.strip()
    descripcion = (descripcion or "").strip()
    if not nombre:
        raise ValueError("El nombre es obligatorio.")

    with _conectar() as conn:
        # verificar que no exista otra app con ese nombre en la misma org
        duplicada = conn.execute(
            "SELECT 1 FROM aplicacion WHERE organizacion_id = %s AND lower(nombre) = lower(%s) AND client_id != %s",
            (organizacion_id, nombre, client_id),
        ).fetchone()
        if duplicada:
            raise NombreAppDuplicado(f"Ya existe una aplicación con el nombre '{nombre}'.")

        fila = conn.execute(
            """
            UPDATE aplicacion
            SET nombre = %s, descripcion = %s
            WHERE client_id = %s AND organizacion_id = %s
            RETURNING client_id, nombre, descripcion
            """,
            (nombre, descripcion, client_id, organizacion_id),
        ).fetchone()

    if fila is None:
        raise ValueError("Aplicación no encontrada.")

    return {"client_id": str(fila[0]), "nombre": fila[1], "descripcion": fila[2]}


def eliminar_aplicacion(client_id, organizacion_id) -> None:
    with _conectar() as conn:
        # Verificar que existe
        app = conn.execute(
            "SELECT client_id FROM aplicacion WHERE client_id = %s AND organizacion_id = %s",
            (client_id, organizacion_id),
        ).fetchone()

        if app is None:
            raise ValueError("Aplicación no encontrada.")

        # Verificar usuarios asociados
        conteo = conn.execute(
            "SELECT COUNT(*) FROM usuario WHERE aplicacion_id = %s",
            (client_id,),
        ).fetchone()[0]

        if conteo > 0:
            raise AplicacionConUsuarios(conteo)

        conn.execute(
            "DELETE FROM aplicacion WHERE client_id = %s AND organizacion_id = %s",
            (client_id, organizacion_id),
        )