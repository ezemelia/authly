import { expirarSesion, obtenerToken } from "./auth.js";

const BASE_API = "/api";

async function llamar(metodo, ruta, cuerpo, token) {
    const encabezados = {};
    if (cuerpo !== undefined) {
        encabezados["Content-Type"] = "application/json";
    }
    if (token !== undefined) {
        encabezados["Authorization"] = "Bearer " + token;
    }

    let respuesta;
    try {
        respuesta = await fetch(BASE_API + ruta, {
            method: metodo,
            headers: encabezados,
            body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo)
        });
    } catch (error) {
        return {ok: false, estado: 0, datos: null};
    }

    let datos = null;
    try {
        datos = await respuesta.json();
    } catch (error) {
        datos = null;
    }
    return {ok: respuesta.ok, estado: respuesta.status, datos: datos};
}

async function llamarConSesion(metodo, ruta, cuerpo) {
    const token = obtenerToken();
    if (token === null) {
        expirarSesion();
        await new Promise(function () {});
    }
    const resultado = await llamar(metodo, ruta, cuerpo, token);
    if (resultado.estado === 401) {
        expirarSesion();
        await new Promise(function () {});
    }
    return resultado;
}

export async function pedirCodigoRecuperacion(datos) {
    // Nunca revela si la cuenta existe: se avisa siempre lo mismo, haya o no haya pasado algo.
    await llamar("POST", "/recovery/codigo", {email: datos.email});
    return {exito: true};
}

export async function cambiarPassword(datos) {
    const resultado = await llamar("POST", "/recovery/confirmar", {
        email: datos.email,
        codigo: datos.codigo,
        password: datos.password
    });
    if (!resultado.ok) {
        if (resultado.datos !== null && typeof resultado.datos.detail === "string") {
            return {exito: false, campo: resultado.datos.campo || "general", mensaje: resultado.datos.detail};
        }
        return {exito: false, campo: "general"};
    }
    return {exito: true};
}

function cuerpoDeRegistro(datos) {
    return {
        nombre: datos.nombre,
        apellido: datos.apellido,
        email: datos.email,
        password: datos.password,
        organizacion: datos.nombreOrg,
        cuit: datos.cuit
    };
}

function traducirErrorRegistro(resultado) {
    if (resultado.estado === 0) {
        return {exito: false, campo: "general", mensaje: "No se pudo conectar con el servidor. Intente nuevamente."};
    }
    if (resultado.estado === 400 && resultado.datos !== null && typeof resultado.datos.detail === "string") {
        let campo = resultado.datos.campo;
        if (campo === undefined || campo === null) {
            campo = "general";
        } else if (campo === "organizacion") {
            campo = "nombreOrg";
        }
        return {exito: false, campo: campo, mensaje: resultado.datos.detail, reinicio: resultado.datos.reinicio === true};
    }
    if (resultado.estado === 422) {
        return {exito: false, campo: "general", mensaje: "Revise los datos ingresados."};
    }
    return {exito: false, campo: "general", mensaje: "No se pudo completar la operación. Intente nuevamente."};
}

export async function pedirCodigo(datos) {
    const resultado = await llamar("POST", "/register/codigo", cuerpoDeRegistro(datos));
    if (!resultado.ok) {
        return traducirErrorRegistro(resultado);
    }
    return {exito: true};
}

export async function confirmarCodigo(datos) {
    const cuerpo = cuerpoDeRegistro(datos);
    cuerpo.codigo = datos.codigo;
    const resultado = await llamar("POST", "/register/confirmar", cuerpo);
    if (!resultado.ok) {
        return traducirErrorRegistro(resultado);
    }
    return {exito: true};
}

export async function iniciarSesion(datos) {
    const login = await llamar("POST", "/login", {email: datos.email, password: datos.password});
    if (login.estado === 401 || login.estado === 422) {
        return {exito: false};
    }
    if (!login.ok || login.datos === null) {
        return {exito: false, motivo: login.estado === 0 ? "red" : "error"};
    }

    const token = login.datos.access_token;
    const perfil = await llamar("GET", "/me", undefined, token);
    if (!perfil.ok || perfil.datos === null) {
        return {exito: false, motivo: perfil.estado === 0 ? "red" : "error"};
    }

    const admin = perfil.datos;
    const organizacion = admin.organizacion || (admin.nombre + " " + admin.apellido);
    return {exito: true, token: token, email: admin.email, organizacion: organizacion};
}

export async function crearAplicacion(datos) {
    const resultado = await llamarConSesion("POST", "/platform/applications/", {nombre: datos.nombre, descripcion: datos.descripcion});
    if (!resultado.ok) {
        if (resultado.estado === 409) {
            return {exito: false, campo: "nombre", mensaje: "Ya existe una aplicación con ese nombre."};
        }
        if (resultado.estado === 0) {
            return {exito: false, campo: "general", mensaje: "No se pudo conectar con el servidor. Intente nuevamente."};
        }
        return {exito: false, campo: "general", mensaje: "No se pudo crear la aplicación. Intente nuevamente."};
    }
    const creada = resultado.datos;
    return {
        exito: true,
        aplicacion: {clientId: creada.client_id, nombre: creada.nombre, descripcion: datos.descripcion.trim()},
        secret: creada.client_secret
    };
}

export async function regenerarSecret(clientId) {
    const resultado = await llamarConSesion("POST", "/platform/applications/" + clientId + "/regenerar-secret", undefined);
    if (!resultado.ok) {
        return {exito: false};
    }
    return {exito: true, secret: resultado.datos.client_secret};
}

export async function editarAplicacion(clientId, datos) {
    const resultado = await llamarConSesion("PUT", "/platform/applications/" + clientId, {nombre: datos.nombre, descripcion: datos.descripcion});
    if (!resultado.ok) {
        if (resultado.estado === 409) {
            return {exito: false, campo: "nombre", mensaje: "Ya existe una aplicación con ese nombre."};
        }
        return {exito: false};
    }
    const editada = resultado.datos;
    return {exito: true, aplicacion: {clientId: editada.client_id, nombre: editada.nombre, descripcion: editada.descripcion}};
}

export async function listarAplicaciones(opciones) {
    const resultado = await llamarConSesion(
        "GET",
        "/platform/applications/?pagina=" + opciones.pagina + "&tamanio=" + opciones.tamanio,
        undefined
    );
    if (!resultado.ok) {
        return {exito: false};
    }

    const datos = resultado.datos;
    return {
        exito: true,
        aplicaciones: datos.aplicaciones.map(function (aplicacion) {
            return {
                clientId: aplicacion.client_id,
                nombre: aplicacion.nombre,
                descripcion: aplicacion.descripcion,
                cantidadUsuarios: aplicacion.cantidad_usuarios
            };
        }),
        total: datos.total_apps,
        totalUsuarios: datos.total_usuarios_organizacion
    };
}

export async function obtenerAplicacion(clientId) {
    const resultado = await llamarConSesion("GET", "/platform/applications/" + clientId, undefined);
    if (!resultado.ok) {
        return {exito: false};
    }
    const a = resultado.datos;
    return {
        exito: true,
        aplicacion: {clientId: a.client_id, nombre: a.nombre, descripcion: a.descripcion},
        cantidadUsuarios: a.cantidad_usuarios
    };
}

export async function eliminarAplicacion(clientId) {
    const resultado = await llamarConSesion("DELETE", "/platform/applications/" + clientId, undefined);
    if (!resultado.ok) {
        if (resultado.estado === 409 && resultado.datos && resultado.datos.motivo === "tiene-usuarios") {
            return {exito: false, motivo: "tiene-usuarios", cantidadUsuarios: resultado.datos.cantidad_usuarios};
        }
        return {exito: false};
    }
    return {exito: true};
}

function traducirRol(rol) {
    return {
        id: rol.id,
        nombre: rol.nombre,
        descripcion: rol.descripcion,
        porDefecto: rol.por_defecto,
        cantidadUsuarios: rol.cantidad_usuarios,
        permisos: rol.permisos
    };
}

function traducirRolGuardado(datos) {
    return {
        exito: true,
        rol: traducirRol(datos.rol),
        rolPorDefectoAnterior: datos.rol_por_defecto_anterior
    };
}

function traducirErrorGuardarRol(resultado) {
    if (resultado.estado === 0) {
        return {exito: false, campo: "general", mensaje: "No se pudo conectar con el servidor. Intente nuevamente."};
    }
    if (resultado.datos !== null && resultado.datos.campo === "nombre") {
        return {exito: false, campo: "nombre", mensaje: resultado.datos.detail};
    }
    return {exito: false};
}

export async function listarRoles(clientId) {
    const resultado = await llamarConSesion("GET", "/platform/applications/" + clientId + "/roles/", undefined);
    if (!resultado.ok) {
        return {exito: false};
    }
    return {exito: true, roles: resultado.datos.roles.map(traducirRol)};
}

export async function crearRol(clientId, datos) {
    const resultado = await llamarConSesion("POST", "/platform/applications/" + clientId + "/roles/", {
        nombre: datos.nombre,
        descripcion: datos.descripcion,
        por_defecto: datos.porDefecto,
        permisos: datos.permisos
    });
    if (!resultado.ok) {
        return traducirErrorGuardarRol(resultado);
    }
    return traducirRolGuardado(resultado.datos);
}

export async function editarRol(clientId, rolId, datos) {
    const resultado = await llamarConSesion("PUT", "/platform/applications/" + clientId + "/roles/" + rolId, {
        nombre: datos.nombre,
        descripcion: datos.descripcion,
        por_defecto: datos.porDefecto,
        permisos: datos.permisos
    });
    if (!resultado.ok) {
        return traducirErrorGuardarRol(resultado);
    }
    return traducirRolGuardado(resultado.datos);
}

export async function eliminarRol(clientId, rolId) {
    const resultado = await llamarConSesion("DELETE", "/platform/applications/" + clientId + "/roles/" + rolId, undefined);
    if (!resultado.ok) {
        if (resultado.estado === 409 && resultado.datos && resultado.datos.motivo === "tiene-usuarios") {
            return {exito: false, motivo: "tiene-usuarios", cantidadUsuarios: resultado.datos.cantidad_usuarios};
        }
        return {exito: false};
    }
    return {exito: true};
}

export async function listarUsuarios(clientId, opciones) {
    const resultado = await llamarConSesion(
        "GET",
        "/platform/applications/" + clientId + "/users/?pagina=" + opciones.pagina + "&tamanio=" + opciones.tamanio,
        undefined
    );
    if (!resultado.ok) {
        return {exito: false};
    }
    return {exito: true, usuarios: resultado.datos.usuarios, total: resultado.datos.total};
}

function traducirErrorUsuario(resultado) {
    const datos = resultado.datos;
    if (datos !== null) {
        if (datos.motivo === "usuario-inexistente") {
            return {exito: false, motivo: "usuario-inexistente"};
        }
        if (datos.motivo === "rol-inexistente") {
            return {exito: false, motivo: "rol-inexistente", rolId: datos.rol_id};
        }
        if (datos.campo && datos.campo !== "general") {
            return {exito: false, campo: datos.campo};
        }
    }
    return {exito: false};
}

export async function editarUsuario(clientId, usuarioId, datos) {
    const resultado = await llamarConSesion("PUT", "/platform/applications/" + clientId + "/users/" + usuarioId, {
        nombre: datos.nombre,
        apellido: datos.apellido,
        roles: datos.roles
    });
    if (!resultado.ok) {
        return traducirErrorUsuario(resultado);
    }
    return {exito: true, usuario: resultado.datos};
}

export async function eliminarUsuario(clientId, usuarioId) {
    const resultado = await llamarConSesion("DELETE", "/platform/applications/" + clientId + "/users/" + usuarioId, undefined);
    if (!resultado.ok) {
        if (resultado.datos !== null && resultado.datos.motivo === "usuario-inexistente") {
            return {exito: false, motivo: "usuario-inexistente"};
        }
        return {exito: false};
    }
    return {exito: true};
}