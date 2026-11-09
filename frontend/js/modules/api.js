import { expirarSesion, obtenerToken } from "./auth.js";

const BASE_API = "/api";

const LISTAR_APLICACIONES_REAL = true; // poné false para volver a la simulación

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

let intentos = 0;
let codigosEmitidos = 0;
let intentosRecuperacion = 0;

let aplicaciones = [
    {clientId: "c3b8f6a2-5d14-4e7a-9b21-7f0e8a4d6c13", nombre: "Authly", descripcion: "Plataforma de autenticación y gestión de roles."},
    {clientId: "9e4a1d70-2b83-4c56-a8f9-31d7b5e02a68", nombre: "Tópico", descripcion: "Aplicación para fidelización de clientes."},
    {clientId: "5a7f20c9-e613-47b8-8d04-b2c91f6a3e57", nombre: "Club Atlético Boca Juniors", descripcion: ""}
];

const aplicacionesGuardadas = localStorage.getItem("simulacion-aplicaciones");
if (aplicacionesGuardadas !== null) {
    aplicaciones = JSON.parse(aplicacionesGuardadas);
}

let roles = [
    {
        id: "1f6d3a52-8c47-4b09-a3e1-6d9c2b7f5e10",
        clientId: "c3b8f6a2-5d14-4e7a-9b21-7f0e8a4d6c13",
        nombre: "Administrador",
        descripcion: "Gestiona usuarios y configuración.",
        porDefecto: false,
        permisos: [
            {recurso: "usuarios", accion: "leer"},
            {recurso: "usuarios", accion: "crear"},
            {recurso: "usuarios", accion: "eliminar"},
            {recurso: "configuracion", accion: "editar"}
        ]
    },
    {
        id: "b82e41c7-5a03-4d96-9f18-0c7e3a6d2b54",
        clientId: "c3b8f6a2-5d14-4e7a-9b21-7f0e8a4d6c13",
        nombre: "Lector",
        descripcion: "Acceso de solo lectura.",
        porDefecto: true,
        permisos: [
            {recurso: "documentos", accion: "leer"}
        ]
    },
    {
        id: "4c90a7e3-d215-48b6-8e0f-93a1b5c7d2e6",
        clientId: "c3b8f6a2-5d14-4e7a-9b21-7f0e8a4d6c13",
        nombre: "Invitado",
        descripcion: "",
        porDefecto: false,
        permisos: []
    },
    {
        id: "e7a3c150-6b92-4f08-b4d7-1a8c5e9f3b26",
        clientId: "9e4a1d70-2b83-4c56-a8f9-31d7b5e02a68",
        nombre: "Cliente",
        descripcion: "",
        porDefecto: true,
        permisos: [
            {recurso: "puntos", accion: "consultar"}
        ]
    }
];

const rolesGuardados = localStorage.getItem("simulacion-roles");
if (rolesGuardados !== null) {
    roles = JSON.parse(rolesGuardados);
}

const idAuthly = "c3b8f6a2-5d14-4e7a-9b21-7f0e8a4d6c13";
const idTopico = "9e4a1d70-2b83-4c56-a8f9-31d7b5e02a68";
const idAdministrador = "1f6d3a52-8c47-4b09-a3e1-6d9c2b7f5e10";
const idLector = "b82e41c7-5a03-4d96-9f18-0c7e3a6d2b54";
const idCliente = "e7a3c150-6b92-4f08-b4d7-1a8c5e9f3b26";

let usuarios = [
    {id: crypto.randomUUID(), clientId: idAuthly, nombre: "Marta", apellido: "Salas", email: "marta.salas@example.com", roles: [idAdministrador, idLector]},
    {id: crypto.randomUUID(), clientId: idAuthly, nombre: "Luis", apellido: "Ferreyra", email: "luis.ferreyra@example.com", roles: [idLector]},
    {id: crypto.randomUUID(), clientId: idAuthly, nombre: "Sofía", apellido: "Benítez", email: "sofia.benitez@example.com", roles: [idLector]}
];

const clientesTopico = [
    ["Agustina", "Acosta", "agustina.acosta@example.com"],
    ["Bruno", "Benítez", "bruno.benitez@example.com"],
    ["Camila", "Cabrera", "camila.cabrera@example.com"],
    ["Damián", "Domínguez", "damian.dominguez@example.com"],
    ["Elena", "Escobar", "elena.escobar@example.com"],
    ["Facundo", "Figueroa", "facundo.figueroa@example.com"],
    ["Guadalupe", "Gómez", "guadalupe.gomez@example.com"],
    ["Hernán", "Herrera", "hernan.herrera@example.com"],
    ["Inés", "Iglesias", "ines.iglesias@example.com"],
    ["Joaquín", "Juárez", "joaquin.juarez@example.com"],
    ["Karina", "Krause", "karina.krause@example.com"],
    ["Lautaro", "Luna", "lautaro.luna@example.com"]
];

for (const cliente of clientesTopico) {
    usuarios.push({id: crypto.randomUUID(), clientId: idTopico, nombre: cliente[0], apellido: cliente[1], email: cliente[2], roles: [idCliente]});
}

const usuariosGuardados = localStorage.getItem("simulacion-usuarios");
if (usuariosGuardados !== null) {
    usuarios = JSON.parse(usuariosGuardados);
}

function guardarRoles() {
    localStorage.setItem("simulacion-roles", JSON.stringify(roles));
}

function guardarAplicaciones() {
    localStorage.setItem("simulacion-aplicaciones", JSON.stringify(aplicaciones));
}

function guardarUsuarios() {
    localStorage.setItem("simulacion-usuarios", JSON.stringify(usuarios));
}

function contarUsuarios(clientId) {
    return usuarios.filter(function (usuario) {
        return usuario.clientId === clientId;
    }).length;
}

function actualizarCantidades() {
    for (const rol of roles) {
        rol.cantidadUsuarios = usuarios.filter(function (usuario) {
            return usuario.roles.includes(rol.id);
        }).length;
    }
}

function describirUsuario(usuario) {
    return {
        id: usuario.id,
        nombre: usuario.nombre,
        apellido: usuario.apellido,
        email: usuario.email,
        roles: usuario.roles.map(function (rolId) {
            const rol = roles.find(function (candidato) {
                return candidato.id === rolId;
            });
            return {id: rol.id, nombre: rol.nombre};
        })
    };
}

actualizarCantidades();

export function esperar(milisegundos) {
    return new Promise(function (resolver) {
        setTimeout(resolver, milisegundos);
    });
}

async function esperarConSesion() {
    await esperar(1000);
    const interruptorActivo = localStorage.getItem("simulacion-token-vencido") !== null;
    if (interruptorActivo || obtenerToken() === null) {
        localStorage.removeItem("simulacion-token-vencido");
        expirarSesion();
        await new Promise(function () {});
    }
}

export async function pedirCodigoRecuperacion(datos) {
    await esperar(1000);
    intentosRecuperacion = 0;
    return {exito: true};
}

export async function cambiarPassword(datos) {
    await esperar(1000);
    if (intentosRecuperacion >= 5) {
        return {exito: false, campo: "codigo"};
    }
    
    if (datos.codigo !== "123456") {
        intentosRecuperacion +=1;
        return {exito: false, campo: "codigo"};
    }
    
    if (datos.password === "Ejemplo123-") {
        return {exito: false, campo: "pass"};
    }
    intentosRecuperacion = 0;
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

async function listarAplicacionesSimulado(opciones) {
    await esperarConSesion();

    const ordenadas = aplicaciones.slice();
    ordenadas.sort(function (a, b) {
        return a.nombre.localeCompare(b.nombre, "es");
    });

    const inicio = (opciones.pagina - 1) * opciones.tamanio;
    const deLaPagina = ordenadas.slice(inicio, inicio + opciones.tamanio);

    return {
        exito: true,
        aplicaciones: deLaPagina.map(function (aplicacion) {
            return {
                clientId: aplicacion.clientId,
                nombre: aplicacion.nombre,
                descripcion: aplicacion.descripcion,
                cantidadUsuarios: contarUsuarios(aplicacion.clientId)
            };
        }),
        total: ordenadas.length,
        totalUsuarios: usuarios.length
    };
}

async function listarAplicacionesReal(opciones) {
    const resultado = await llamarConSesion("GET", "/platform/applications/", undefined);
    if (!resultado.ok) {
        return {exito: false};
    }

    const todas = resultado.datos.slice();
    todas.sort(function (a, b) {
        return a.nombre.localeCompare(b.nombre, "es");
    });

    const inicio = (opciones.pagina - 1) * opciones.tamanio;
    const deLaPagina = todas.slice(inicio, inicio + opciones.tamanio);

    return {
        exito: true,
        aplicaciones: deLaPagina.map(function (aplicacion) {
            return {
                clientId: aplicacion.client_id,
                nombre: aplicacion.nombre,
                descripcion: aplicacion.descripcion,
                // El backend todavía no informa cuántos usuarios tiene cada aplicación.
                cantidadUsuarios: null
            };
        }),
        total: todas.length,
        // El backend todavía no informa el total de usuarios de la organización.
        totalUsuarios: null
    };
}

export async function listarAplicaciones(opciones) {
    if (LISTAR_APLICACIONES_REAL) {
        return listarAplicacionesReal(opciones);
    }
    return listarAplicacionesSimulado(opciones);
}

export async function obtenerAplicacion(clientId) {
    await esperarConSesion();
    const encontrada = aplicaciones.find(function (candidata) {
        return candidata.clientId === clientId;
    });
    if (encontrada === undefined) {
        return {exito: false};
    }
    return {exito: true, aplicacion: encontrada, cantidadUsuarios: contarUsuarios(clientId)};
}

export async function listarRoles(clientId) {
    await esperarConSesion();

    const existe = aplicaciones.some(function (candidata) {
        return candidata.clientId === clientId;
    });
    if (!existe) {
        return {exito: false};
    }

    const rolesDeLaApp = roles.filter(function (rol) {
        return rol.clientId === clientId;
    });
    rolesDeLaApp.sort(function (a, b) {
        return a.nombre.localeCompare(b.nombre, "es");
    });
    return {exito: true, roles: rolesDeLaApp};
}

export async function crearRol(clientId, datos) {
    await esperarConSesion();

    const existe = aplicaciones.some(function (candidata) {
        return candidata.clientId === clientId;
    });
    if (!existe) {
        return {exito: false};
    }

    const nombreNuevo = datos.nombre.trim().toLowerCase();
    const yaExiste = roles.some(function (rol) {
        return rol.clientId === clientId && rol.nombre.trim().toLowerCase() === nombreNuevo;
    });
    if (yaExiste) {
        return {exito: false, campo: "nombre", mensaje: "Ya existe un rol con ese nombre."};
    }

    let anterior = null;
    if (datos.porDefecto) {
        const actual = roles.find(function (rol) {
            return rol.clientId === clientId && rol.porDefecto;
        });
        if (actual !== undefined) {
            actual.porDefecto = false;
            anterior = actual.nombre;
        }
    }

    const rolNuevo = {
        id: crypto.randomUUID(),
        clientId: clientId,
        nombre: datos.nombre.trim(),
        descripcion: datos.descripcion.trim(),
        porDefecto: datos.porDefecto,
        permisos: datos.permisos,
        cantidadUsuarios: 0
    };

    roles.push(rolNuevo);
    guardarRoles();

    return {exito: true, rol: rolNuevo, rolPorDefectoAnterior: anterior};
}

export async function editarRol(clientId, rolId, datos) {
    await esperarConSesion();

    const rol = roles.find(function (candidato) {
        return candidato.id === rolId && candidato.clientId === clientId;
    });
    if (rol === undefined) {
        return {exito: false};
    }

    const nombreNuevo = datos.nombre.trim().toLowerCase();
    const yaExiste = roles.some(function (otro) {
        return otro.clientId === clientId && otro.id !== rolId && otro.nombre.trim().toLowerCase() === nombreNuevo;
    });
    if (yaExiste) {
        return {exito: false, campo: "nombre", mensaje: "Ya existe un rol con ese nombre."};
    }

    let anterior = null;
    if (datos.porDefecto && !rol.porDefecto) {
        const actual = roles.find(function (otro) {
            return otro.clientId === clientId && otro.porDefecto;
        });
        if (actual !== undefined) {
            actual.porDefecto = false;
            anterior = actual.nombre;
        }
    }

    rol.nombre = datos.nombre.trim();
    rol.descripcion = datos.descripcion.trim();
    rol.permisos = datos.permisos;
    rol.porDefecto = datos.porDefecto;
    guardarRoles();

    return {exito: true, rol: rol, rolPorDefectoAnterior: anterior};
}

export async function eliminarRol(clientId, rolId) {
    await esperarConSesion();

    const rol = roles.find(function (candidato) {
        return candidato.id === rolId && candidato.clientId === clientId;
    });
    if (rol === undefined) {
        return {exito: false};
    }

    if (rol.cantidadUsuarios > 0) {
        return {exito: false, motivo: "tiene-usuarios", cantidadUsuarios: rol.cantidadUsuarios};
    }

    roles = roles.filter(function (otro) {
        return otro.id !== rolId;
    });
    guardarRoles();

    return {exito: true, rol: rol};
}

export async function eliminarAplicacion(clientId) {
    await esperarConSesion();

    const aplicacion = aplicaciones.find(function (candidata) {
        return candidata.clientId === clientId;
    });
    if (aplicacion === undefined) {
        return {exito: false};
    }

    const usuariosDeLaApp = contarUsuarios(clientId);
    if (usuariosDeLaApp > 0) {
        return {exito: false, motivo: "tiene-usuarios", cantidadUsuarios: usuariosDeLaApp};
    }

    const cantidadRoles = roles.filter(function (rol) {
        return rol.clientId === clientId;
    }).length;

    aplicaciones = aplicaciones.filter(function (otra) {
        return otra.clientId !== clientId;
    });
    roles = roles.filter(function (rol) {
        return rol.clientId !== clientId;
    });
    guardarAplicaciones();
    guardarRoles();

    return {exito: true, aplicacion: aplicacion, rolesEliminados: cantidadRoles};
}

export async function listarUsuarios(clientId, opciones) {
    await esperarConSesion();

    const existe = aplicaciones.some(function (candidata) {
        return candidata.clientId === clientId;
    });
    if (!existe) {
        return {exito: false};
    }

    const deLaApp = usuarios.filter(function (usuario) {
        return usuario.clientId === clientId;
    });
    deLaApp.sort(function (a, b) {
        const porApellido = a.apellido.localeCompare(b.apellido, "es");
        if (porApellido !== 0) {
            return porApellido;
        }
        return a.nombre.localeCompare(b.nombre, "es");
    });

    const inicio = (opciones.pagina - 1) * opciones.tamanio;
    const deLaPagina = deLaApp.slice(inicio, inicio + opciones.tamanio);

    return {exito: true, usuarios: deLaPagina.map(describirUsuario), total: deLaApp.length};
}

export async function editarUsuario(clientId, usuarioId, datos) {
    await esperarConSesion();

    const usuario = usuarios.find(function (candidato) {
        return candidato.id === usuarioId && candidato.clientId === clientId;
    });
    if (usuario === undefined) {
        return {exito: false, motivo: "usuario-inexistente"};
    }

    if (datos.nombre.trim() === "") {
        return {exito: false, campo: "nombre"};
    }
    if (datos.apellido.trim() === "") {
        return {exito: false, campo: "apellido"};
    }
    if (datos.roles.length === 0) {
        return {exito: false, campo: "roles"};
    }

    for (const rolId of datos.roles) {
        const existeRol = roles.some(function (rol) {
            return rol.id === rolId && rol.clientId === clientId;
        });
        if (!existeRol) {
            return {exito: false, motivo: "rol-inexistente", rolId: rolId};
        }
    }

    usuario.nombre = datos.nombre.trim();
    usuario.apellido = datos.apellido.trim();
    usuario.roles = datos.roles.slice();
    actualizarCantidades();
    guardarUsuarios();
    guardarRoles();

    return {exito: true, usuario: describirUsuario(usuario)};
}

export async function eliminarUsuario(clientId, usuarioId) {
    await esperarConSesion();

    const usuario = usuarios.find(function (candidato) {
        return candidato.id === usuarioId && candidato.clientId === clientId;
    });
    if (usuario === undefined) {
        return {exito: false, motivo: "usuario-inexistente"};
    }

    const eliminado = describirUsuario(usuario);
    usuarios = usuarios.filter(function (otro) {
        return otro.id !== usuarioId;
    });
    actualizarCantidades();
    guardarUsuarios();
    guardarRoles();

    return {exito: true, usuario: eliminado};
}