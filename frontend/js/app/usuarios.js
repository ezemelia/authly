import { listarUsuarios } from "../modules/api.js";
import { crearPaginador } from "../modules/components.js";
import { estado } from "./estado.js";

const TAMANIO = 10;

let lista = null;
let paginador = null;
let alEditar = null;
let alEliminar = null;
let paginaActual = 1;
let yaCargo = false;

function crearFilaUsuario(usuario) {
    const fila = document.createElement("tr");

    const celdaNombre = document.createElement("td");
    celdaNombre.textContent = usuario.apellido + ", " + usuario.nombre;

    const celdaEmail = document.createElement("td");
    celdaEmail.dataset.etiqueta = "Email";
    celdaEmail.textContent = usuario.email;

    const celdaRoles = document.createElement("td");
    celdaRoles.dataset.etiqueta = "Roles";
    for (const rol of usuario.roles) {
        const etiqueta = document.createElement("span");
        etiqueta.classList.add("etiqueta-rol");
        etiqueta.textContent = rol.nombre;
        celdaRoles.append(etiqueta);
    }

    const celdaAcciones = document.createElement("td");
    const acciones = document.createElement("div");
    acciones.classList.add("acciones-fila");

    const botonEditar = document.createElement("button");
    botonEditar.type = "button";
    botonEditar.textContent = "Editar";
    botonEditar.classList.add("boton-secundario", "boton-chico");
    botonEditar.setAttribute("aria-label", "Editar usuario " + usuario.nombre + " " + usuario.apellido);
    botonEditar.addEventListener("click", function () {
        alEditar(usuario);
    });

    const botonEliminar = document.createElement("button");
    botonEliminar.type = "button";
    botonEliminar.textContent = "Eliminar";
    botonEliminar.classList.add("boton-peligro-borde", "boton-chico");
    botonEliminar.setAttribute("aria-label", "Eliminar usuario " + usuario.nombre + " " + usuario.apellido);
    botonEliminar.addEventListener("click", function () {
        alEliminar(usuario);
    });

    acciones.append(botonEditar, botonEliminar);
    celdaAcciones.append(acciones);

    fila.append(celdaNombre, celdaEmail, celdaRoles, celdaAcciones);
    return fila;
}

function mostrarUsuarios(usuarios, total) {
    estado.cantidadUsuarios = total;
    lista.carga.classList.add("oculto");
    lista.cuerpo.replaceChildren();
    for (const usuario of usuarios) {
        lista.cuerpo.append(crearFilaUsuario(usuario));
    }
    if (total === 0) {
        lista.tabla.classList.add("oculto");
        lista.vacio.classList.remove("oculto");
    } else {
        lista.tabla.classList.remove("oculto");
        lista.vacio.classList.add("oculto");
    }
    paginador.mostrar(paginaActual, total, TAMANIO);
}

export async function cargarUsuarios() {
    lista.carga.textContent = "Cargando usuarios...";
    lista.carga.classList.remove("oculto");
    lista.tabla.classList.add("oculto");
    lista.vacio.classList.add("oculto");
    lista.navPaginador.classList.add("oculto");

    const respuesta = await listarUsuarios(estado.aplicacionActual.clientId, {pagina: paginaActual, tamanio: TAMANIO});
    if (!respuesta.exito) {
        lista.carga.textContent = "No se pudieron cargar los usuarios. Recargue la página.";
        return;
    }

    const ultimaPagina = Math.max(1, Math.ceil(respuesta.total / TAMANIO));
    if (paginaActual > ultimaPagina) {
        paginaActual = ultimaPagina;
        await cargarUsuarios();
        return;
    }

    mostrarUsuarios(respuesta.usuarios, respuesta.total);
}

export function cargarUsuariosSiHaceFalta() {
    if (yaCargo) {
        return;
    }
    yaCargo = true;
    cargarUsuarios();
}

export function marcarUsuariosDesactualizados() {
    yaCargo = false;
}

export function iniciarUsuarios(opciones) {
    lista = {
        carga: document.getElementById("estado-carga-usuarios"),
        tabla: document.getElementById("tabla-usuarios"),
        cuerpo: document.getElementById("cuerpo-tabla-usuarios"),
        vacio: document.getElementById("estado-vacio-usuarios"),
        navPaginador: document.getElementById("paginador-usuarios")
    };
    paginador = crearPaginador(lista.navPaginador, function (pagina) {
        paginaActual = pagina;
        cargarUsuarios();
    });
    alEditar = opciones.alEditar;
    alEliminar = opciones.alEliminar;
}