import { obtenerAplicacion } from "../modules/api.js";
import { activarCopia } from "../modules/components.js";
import { obtenerParametro } from "../modules/utils.js";
import { estado } from "./estado.js";
import { cargarRoles } from "./roles.js";

let detalle = null;

export function mostrarDatos(aplicacion) {
    detalle.titulo.textContent = aplicacion.nombre;
    detalle.clientId.textContent = aplicacion.clientId;
    if (aplicacion.descripcion === "") {
        detalle.descripcion.classList.add("oculto");
    } else {
        detalle.descripcion.textContent = aplicacion.descripcion;
        detalle.descripcion.classList.remove("oculto");
    }
    document.title = aplicacion.nombre + " | Authly";
}

export async function cargarAplicacion() {
    const clientId = obtenerParametro("id");
    const respuesta = await obtenerAplicacion(clientId);
    detalle.carga.classList.add("oculto");

    if (respuesta.exito) {
        estado.aplicacionActual = respuesta.aplicacion;
        estado.cantidadUsuarios = respuesta.cantidadUsuarios;
        mostrarDatos(estado.aplicacionActual);
        cargarRoles();
        detalle.contenido.classList.remove("oculto");
    } else {
        detalle.noEncontrada.classList.remove("oculto");
    }
}

export function iniciarAplicacion() {
    detalle = {
        carga: document.getElementById("estado-carga"),
        contenido: document.getElementById("detalle-app"),
        noEncontrada: document.getElementById("no-encontrada"),
        titulo: document.getElementById("titulo-detalle"),
        descripcion: document.getElementById("descripcion-detalle"),
        clientId: document.getElementById("credencial-client-id"),
        botonCopiar: document.getElementById("boton-copiar-client-id")
    };

    activarCopia(detalle.botonCopiar, function () {
        return detalle.clientId.textContent;
    });
}