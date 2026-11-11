"""CU-06: gestión de los usuarios de una aplicación desde el panel (listar, editar, eliminar).

Los usuarios se crean solo por el registro vía API (CU-05) y el email no se puede cambiar.
"""
from app.database import obtener_conexion

MAX_NOMBRE = 100


class AplicacionNoEncontrada(Exception):
    pass


class UsuarioNoEncontrado(Exception):
    pass


class RolInexistente(Exception):
    def __init__(self, rol_id):
        super().__init__("Alguno de los roles indicados ya no existe.")
        self.rol_id = str(rol_id)


class UsuarioInvalido(Exception):
    def __init__(self, mensaje: str, campo: str):
        super().__init__(mensaje)
        self.campo = campo


def _conectar():
    conexion = obtener_conexion()
    if conexion is None:
        raise RuntimeError("No se pudo conectar a la base de datos")
    return conexion


def _verificar_aplicacion(conn, client_id, organizacion_id) -> None:
    if conn.execute(
        "SELECT 1 FROM aplicacion WHERE client_id = %s AND organizacion_id = %s", (client_id, organizacion_id)
    ).fetchone() is None:
        raise AplicacionNoEncontrada("Aplicación no encontrada.")


def _roles_de(conn, usuario_ids) -> dict:
    roles = {u: [] for u in usuario_ids}
    if not usuario_ids:
        return roles
    filas = conn.execute(
        """
        SELECT ur.usuario_id, r.id, r.nombre
        FROM usuario_rol ur JOIN rol r ON r.id = ur.rol_id
        WHERE ur.usuario_id = ANY(%s)
        ORDER BY r.nombre COLLATE "es-AR-x-icu"
        """,
        (list(usuario_ids),),
    ).fetchall()
    for usuario_id, rol_id, nombre in filas:
        roles[usuario_id].append({"id": str(rol_id), "nombre": nombre})
    return roles


def _usuario(conn, client_id, usuario_id) -> dict | None:
    fila = conn.execute(
        "SELECT id, nombre, apellido, email FROM usuario WHERE id = %s AND aplicacion_id = %s",
        (usuario_id, client_id),
    ).fetchone()
    if fila is None:
        return None
    return {
        "id": str(fila[0]), "nombre": fila[1], "apellido": fila[2], "email": fila[3],
        "roles": _roles_de(conn, [fila[0]])[fila[0]],
    }


def listar_usuarios(client_id, organizacion_id, pagina: int = 1, tamanio: int = 10) -> dict:
    pagina = max(pagina, 1)
    tamanio = min(max(tamanio, 1), 100)
    with _conectar() as conn:
        _verificar_aplicacion(conn, client_id, organizacion_id)
        total = conn.execute("SELECT COUNT(*) FROM usuario WHERE aplicacion_id = %s", (client_id,)).fetchone()[0]
        filas = conn.execute(
            """
            SELECT id, nombre, apellido, email FROM usuario
            WHERE aplicacion_id = %s
            ORDER BY apellido COLLATE "es-AR-x-icu", nombre COLLATE "es-AR-x-icu", id
            LIMIT %s OFFSET %s
            """,
            (client_id, tamanio, (pagina - 1) * tamanio),
        ).fetchall()
        roles = _roles_de(conn, [f[0] for f in filas])
    return {
        "usuarios": [
            {"id": str(f[0]), "nombre": f[1], "apellido": f[2], "email": f[3], "roles": roles[f[0]]} for f in filas
        ],
        "total": total,
        "pagina": pagina,
        "tamanio": tamanio,
    }


def editar_usuario(client_id, usuario_id, organizacion_id, nombre, apellido, roles) -> dict:
    nombre, apellido = nombre.strip(), apellido.strip()
    if not nombre:
        raise UsuarioInvalido("El nombre es obligatorio.", "nombre")
    if not apellido:
        raise UsuarioInvalido("El apellido es obligatorio.", "apellido")
    if len(nombre) > MAX_NOMBRE:
        raise UsuarioInvalido(f"El nombre no puede superar los {MAX_NOMBRE} caracteres.", "nombre")
    if len(apellido) > MAX_NOMBRE:
        raise UsuarioInvalido(f"El apellido no puede superar los {MAX_NOMBRE} caracteres.", "apellido")
    roles = list(dict.fromkeys(roles))  # sin repetidos, conservando el orden
    if not roles:
        raise UsuarioInvalido("El usuario debe tener al menos un rol.", "roles")

    # todo en una transacción: o se aplican nombre, apellido y roles, o no cambia nada
    with _conectar() as conn:
        _verificar_aplicacion(conn, client_id, organizacion_id)
        if conn.execute(
            "SELECT 1 FROM usuario WHERE id = %s AND aplicacion_id = %s FOR UPDATE", (usuario_id, client_id)
        ).fetchone() is None:
            raise UsuarioNoEncontrado("El usuario ya no existe.")

        existentes = {
            f[0] for f in conn.execute(
                "SELECT id FROM rol WHERE aplicacion_id = %s AND id = ANY(%s) FOR SHARE", (client_id, roles)
            ).fetchall()
        }
        for rol_id in roles:
            if rol_id not in existentes:
                raise RolInexistente(rol_id)

        conn.execute("UPDATE usuario SET nombre = %s, apellido = %s WHERE id = %s", (nombre, apellido, usuario_id))
        conn.execute("DELETE FROM usuario_rol WHERE usuario_id = %s", (usuario_id,))
        for rol_id in roles:
            conn.execute(
                "INSERT INTO usuario_rol (usuario_id, rol_id, aplicacion_id) VALUES (%s, %s, %s)",
                (usuario_id, rol_id, client_id),
            )
        return _usuario(conn, client_id, usuario_id)


def eliminar_usuario(client_id, usuario_id, organizacion_id) -> dict:
    with _conectar() as conn:
        _verificar_aplicacion(conn, client_id, organizacion_id)
        usuario = _usuario(conn, client_id, usuario_id)
        if usuario is None:
            raise UsuarioNoEncontrado("El usuario ya no existe.")
        conn.execute("DELETE FROM usuario WHERE id = %s", (usuario_id,))  # sus asignaciones se borran en cascada
    return usuario
