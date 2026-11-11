import unicodedata

import psycopg

from app.database import obtener_conexion

MAX_NOMBRE = 100
MAX_DESCRIPCION = 500
MAX_PERMISO = 100


class AplicacionNoEncontrada(Exception):
    pass


class RolNoEncontrado(Exception):
    pass


class RolInvalido(Exception):
    """Dato inválido. `campo` indica qué campo del formulario marcar."""

    def __init__(self, mensaje: str, campo: str):
        super().__init__(mensaje)
        self.campo = campo


class NombreRolDuplicado(Exception):
    pass


class RolConUsuarios(Exception):
    def __init__(self, cantidad: int):
        super().__init__(f"El rol tiene {cantidad} usuario(s) asignado(s).")
        self.cantidad = cantidad


def _conectar():
    conexion = obtener_conexion()
    if conexion is None:
        raise RuntimeError("No se pudo conectar a la base de datos")
    return conexion


def _verificar_aplicacion(conn, client_id, organizacion_id) -> None:
    # aísla organizaciones: solo se gestionan roles de aplicaciones de la organización del administrador
    if conn.execute(
        "SELECT 1 FROM aplicacion WHERE client_id = %s AND organizacion_id = %s", (client_id, organizacion_id)
    ).fetchone() is None:
        raise AplicacionNoEncontrada("Aplicación no encontrada.")


def _clave_orden(texto: str):
    # orden alfabético español: sin distinguir mayúsculas ni tildes
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return sin_tildes.casefold(), texto.casefold()


def _validar(nombre: str, descripcion: str, permisos: list) -> tuple:
    nombre = nombre.strip()
    descripcion = (descripcion or "").strip()
    if not nombre:
        raise RolInvalido("El nombre es obligatorio.", "nombre")
    if len(nombre) > MAX_NOMBRE:
        raise RolInvalido(f"El nombre no puede superar los {MAX_NOMBRE} caracteres.", "nombre")
    if len(descripcion) > MAX_DESCRIPCION:
        raise RolInvalido(f"La descripción no puede superar los {MAX_DESCRIPCION} caracteres.", "descripcion")

    # recurso y acción se guardan normalizados (minúsculas, sin espacios en los extremos)
    normalizados, vistos = [], set()
    for permiso in permisos:
        recurso = permiso["recurso"].strip().lower()
        accion = permiso["accion"].strip().lower()
        if not recurso or not accion:
            raise RolInvalido("Cada permiso debe tener recurso y acción.", "permisos")
        if len(recurso) > MAX_PERMISO or len(accion) > MAX_PERMISO:
            raise RolInvalido(f"Recurso y acción no pueden superar los {MAX_PERMISO} caracteres.", "permisos")
        if (recurso, accion) in vistos:
            raise RolInvalido(f"El permiso {recurso} + {accion} está repetido.", "permisos")
        vistos.add((recurso, accion))
        normalizados.append({"recurso": recurso, "accion": accion})
    return nombre, descripcion, normalizados


def _rol_completo(conn, rol_id) -> dict:
    fila = conn.execute(
        """
        SELECT r.id, r.nombre, r.descripcion, r.por_defecto,
               (SELECT COUNT(*) FROM usuario_rol ur WHERE ur.rol_id = r.id)
        FROM rol r WHERE r.id = %s
        """,
        (rol_id,),
    ).fetchone()
    permisos = conn.execute(
        "SELECT recurso, accion FROM permiso WHERE rol_id = %s ORDER BY recurso, accion", (rol_id,)
    ).fetchall()
    return {
        "id": str(fila[0]),
        "nombre": fila[1],
        "descripcion": fila[2],
        "por_defecto": fila[3],
        "cantidad_usuarios": fila[4],
        "permisos": [{"recurso": p[0], "accion": p[1]} for p in permisos],
    }


def listar_roles(client_id, organizacion_id) -> list:
    with _conectar() as conn:
        _verificar_aplicacion(conn, client_id, organizacion_id)
        ids = [f[0] for f in conn.execute("SELECT id FROM rol WHERE aplicacion_id = %s", (client_id,)).fetchall()]
        roles = [_rol_completo(conn, rol_id) for rol_id in ids]
    return sorted(roles, key=lambda r: _clave_orden(r["nombre"]))


def _desmarcar_por_defecto_anterior(conn, client_id, excepto_id=None):
    """Quita la marca al rol por defecto actual y devuelve su nombre (o None)."""
    fila = conn.execute(
        "SELECT id, nombre FROM rol WHERE aplicacion_id = %s AND por_defecto AND id IS DISTINCT FROM %s",
        (client_id, excepto_id),
    ).fetchone()
    if fila is None:
        return None
    conn.execute("UPDATE rol SET por_defecto = false WHERE id = %s", (fila[0],))
    return fila[1]


def _nombre_en_uso(conn, client_id, nombre, excepto_id=None) -> bool:
    return conn.execute(
        "SELECT 1 FROM rol WHERE aplicacion_id = %s AND lower(nombre) = lower(%s) AND id IS DISTINCT FROM %s",
        (client_id, nombre, excepto_id),
    ).fetchone() is not None


def _guardar_permisos(conn, rol_id, permisos):
    conn.execute("DELETE FROM permiso WHERE rol_id = %s", (rol_id,))
    for p in permisos:
        conn.execute(
            "INSERT INTO permiso (rol_id, recurso, accion) VALUES (%s, %s, %s)", (rol_id, p["recurso"], p["accion"])
        )


def crear_rol(client_id, organizacion_id, nombre, descripcion, por_defecto, permisos) -> dict:
    nombre, descripcion, permisos = _validar(nombre, descripcion, permisos)
    try:
        with _conectar() as conn:
            _verificar_aplicacion(conn, client_id, organizacion_id)
            if _nombre_en_uso(conn, client_id, nombre):
                raise NombreRolDuplicado("Ya existe un rol con ese nombre.")
            # orden de la guía de la base: desmarcar el rol por defecto anterior antes de marcar el nuevo
            anterior = _desmarcar_por_defecto_anterior(conn, client_id) if por_defecto else None
            rol_id = conn.execute(
                "INSERT INTO rol (aplicacion_id, nombre, descripcion, por_defecto) VALUES (%s, %s, %s, %s) RETURNING id",
                (client_id, nombre, descripcion, por_defecto),
            ).fetchone()[0]
            _guardar_permisos(conn, rol_id, permisos)
            rol = _rol_completo(conn, rol_id)
    except psycopg.errors.UniqueViolation:
        # otra sesión creó el mismo nombre (o marcó otro rol por defecto) en el mismo instante
        raise NombreRolDuplicado("Ya existe un rol con ese nombre.")
    return {"rol": rol, "rol_por_defecto_anterior": anterior}


def editar_rol(client_id, rol_id, organizacion_id, nombre, descripcion, por_defecto, permisos) -> dict:
    nombre, descripcion, permisos = _validar(nombre, descripcion, permisos)
    try:
        with _conectar() as conn:
            _verificar_aplicacion(conn, client_id, organizacion_id)
            actual = conn.execute(
                "SELECT por_defecto FROM rol WHERE id = %s AND aplicacion_id = %s FOR UPDATE", (rol_id, client_id)
            ).fetchone()
            if actual is None:
                raise RolNoEncontrado("El rol ya no existe.")
            if _nombre_en_uso(conn, client_id, nombre, rol_id):
                raise NombreRolDuplicado("Ya existe un rol con ese nombre.")
            anterior = None
            if por_defecto and not actual[0]:
                anterior = _desmarcar_por_defecto_anterior(conn, client_id, rol_id)
            conn.execute(
                "UPDATE rol SET nombre = %s, descripcion = %s, por_defecto = %s WHERE id = %s",
                (nombre, descripcion, por_defecto, rol_id),
            )
            _guardar_permisos(conn, rol_id, permisos)
            rol = _rol_completo(conn, rol_id)
    except psycopg.errors.UniqueViolation:
        raise NombreRolDuplicado("Ya existe un rol con ese nombre.")
    return {"rol": rol, "rol_por_defecto_anterior": anterior}


def eliminar_rol(client_id, rol_id, organizacion_id) -> dict:
    try:
        with _conectar() as conn:
            _verificar_aplicacion(conn, client_id, organizacion_id)
            fila = conn.execute(
                "SELECT nombre, por_defecto FROM rol WHERE id = %s AND aplicacion_id = %s FOR UPDATE",
                (rol_id, client_id),
            ).fetchone()
            if fila is None:
                raise RolNoEncontrado("El rol ya no existe.")
            asignados = conn.execute("SELECT COUNT(*) FROM usuario_rol WHERE rol_id = %s", (rol_id,)).fetchone()[0]
            if asignados > 0:
                raise RolConUsuarios(asignados)
            conn.execute("DELETE FROM rol WHERE id = %s", (rol_id,))  # los permisos se borran en cascada
    except psycopg.errors.ForeignKeyViolation:
        # entre la verificación y el borrado, un usuario recibió el rol (por ejemplo, al registrarse)
        raise RolConUsuarios(1)
    return {"id": str(rol_id), "nombre": fila[0], "por_defecto": fila[1]}
