import { listarRoles } from "../modules/api.js";
import { estado } from "./estado.js";

let lista = null;
let alEditar = null;
let alEliminar = null;

function crearFilaRol(rol) {
    const fila = document.createElement("tr");

    const celdaNombre = document.createElement("td");
    celdaNombre.textContent = rol.nombre;
    if (rol.porDefecto) {
        const etiqueta = document.createElement("span");
        etiqueta.classList.add("etiqueta-predeterminado");
        etiqueta.textContent = "Predeterminado";
        celdaNombre.append(etiqueta);
    }
    if (rol.descripcion !== "") {
        const descripcion = document.createElement("span");
        descripcion.classList.add("descripcion");
        descripcion.textContent = rol.descripcion;
        celdaNombre.append(descripcion);
    }

    const celdaPermisos = document.createElement("td");
    celdaPermisos.dataset.etiqueta = "Permisos";
    if (rol.permisos.length === 0) {
        const sinPermisos = document.createElement("span");
        sinPermisos.classList.add("descripcion");
        sinPermisos.textContent = "Sin permisos";
        celdaPermisos.append(sinPermisos);
    } else {
        for (const permiso of rol.permisos) {
            const etiqueta = document.createElement("span");
            etiqueta.classList.add("etiqueta-permiso");
            etiqueta.textContent = permiso.recurso + " · " + permiso.accion;
            celdaPermisos.append(etiqueta);
        }
    }

    const celdaUsuarios = document.createElement("td");
    celdaUsuarios.dataset.etiqueta = "Usuarios";
    celdaUsuarios.textContent = rol.cantidadUsuarios;

    const celdaAcciones = document.createElement("td");
    const acciones = document.createElement("div");
    acciones.classList.add("acciones-fila");

    const botonEditar = document.createElement("button");
    botonEditar.type = "button";
    botonEditar.textContent = "Editar";
    botonEditar.classList.add("boton-secundario", "boton-chico");
    botonEditar.setAttribute("aria-label", "Editar rol " + rol.nombre);
    botonEditar.addEventListener("click", function () {
        alEditar(rol);
    });

    const botonEliminar = document.createElement("button");
    botonEliminar.type = "button";
    botonEliminar.textContent = "Eliminar";
    botonEliminar.classList.add("boton-peligro-borde", "boton-chico");
    botonEliminar.setAttribute("aria-label", "Eliminar rol " + rol.nombre);
    botonEliminar.addEventListener("click", function () {
        alEliminar(rol);
    });

    acciones.append(botonEditar, botonEliminar);
    celdaAcciones.append(acciones);

    fila.append(celdaNombre, celdaPermisos, celdaUsuarios, celdaAcciones);
    return fila;
}

function mostrarRoles(roles) {
    estado.roles = roles;
    estado.cantidadRoles = roles.length;
    lista.carga.classList.add("oculto");
    lista.cuerpo.replaceChildren();
    for (const rol of roles) {
        lista.cuerpo.append(crearFilaRol(rol));
    }
    if (roles.length === 0) {
        lista.tabla.classList.add("oculto");
        lista.vacio.classList.remove("oculto");
    } else {
        lista.tabla.classList.remove("oculto");
        lista.vacio.classList.add("oculto");
    }
}

export async function cargarRoles() {
    const respuesta = await listarRoles(estado.aplicacionActual.clientId);
    if (!respuesta.exito) {
        lista.carga.textContent = "No se pudieron cargar los roles. Recargue la página.";
        return;
    }
    mostrarRoles(respuesta.roles);
}

export function iniciarRoles(opciones) {
    lista = {
        carga: document.getElementById("estado-carga-roles"),
        tabla: document.getElementById("tabla-roles"),
        cuerpo: document.getElementById("cuerpo-tabla-roles"),
        vacio: document.getElementById("estado-vacio-roles")
    };
    alEditar = opciones.alEditar;
    alEliminar = opciones.alEliminar;
}