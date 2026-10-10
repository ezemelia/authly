import { eliminarAplicacion } from "../modules/api.js";
import { mostrarError, guardarAvisoPendiente } from "../modules/notifications.js";
import { normalizar, textoUsuarios } from "../modules/utils.js";
import { estado } from "./estado.js";

function textoRolesDeLaApp(cantidad) {
    if (cantidad === null) {
        return " y, si los tiene, sus roles";
    }
    if (cantidad === 0) {
        return "";
    }
    if (cantidad === 1) {
        return " y su rol";
    }
    return " y sus " + cantidad + " roles";
}

export function iniciarEliminarApp() {
    const eliminarAppModal = {
        botonAbrir: document.getElementById("boton-eliminar-app"),
        modal: document.getElementById("modal-eliminar-app"),
        titulo: document.getElementById("titulo-eliminar-app"),
        aviso: document.getElementById("aviso-eliminar-app"),
        bloqueNombre: document.getElementById("confirmacion-nombre-app"),
        campoNombre: document.getElementById("campo-nombre-eliminar"),
        ayudaNombre: document.getElementById("ayuda-nombre-eliminar"),
        error: document.getElementById("error-eliminar-app"),
        botonConfirmar: document.getElementById("boton-confirmar-eliminar-app"),
        botonCancelar: document.getElementById("boton-cancelar-eliminar-app")
    };

    function prepararEliminarApp() {
        eliminarAppModal.error.classList.add("oculto");
        eliminarAppModal.campoNombre.value = "";

        if (estado.cantidadUsuarios > 0) {
            eliminarAppModal.titulo.textContent = "No se puede eliminar la aplicación";
            const consejo = estado.cantidadUsuarios === 1 ? "Elimínelo" : "Elimínelos";
            eliminarAppModal.aviso.textContent = "La aplicación «" + estado.aplicacionActual.nombre + "» tiene " + textoUsuarios(estado.cantidadUsuarios) + ". " + consejo + " desde la pestaña «Usuarios» y luego vuelva a intentarlo.";
            eliminarAppModal.bloqueNombre.classList.add("oculto");
            eliminarAppModal.botonConfirmar.classList.add("oculto");
            eliminarAppModal.botonCancelar.textContent = "Entendido";
        } else {
            eliminarAppModal.titulo.textContent = "Eliminar aplicación";
            const hayRoles = estado.cantidadRoles !== null && estado.cantidadRoles > 0;
            const verbo = hayRoles ? "Se eliminarán" : "Se eliminará";
            eliminarAppModal.aviso.textContent = verbo + " la aplicación «" + estado.aplicacionActual.nombre + "»" + textoRolesDeLaApp(estado.cantidadRoles) + ". Los sistemas que usan su client ID y su client secret dejarán de funcionar. Esta acción no se puede deshacer.";
            eliminarAppModal.ayudaNombre.textContent = "Escriba «" + estado.aplicacionActual.nombre + "». No importan las mayúsculas ni los espacios sobrantes.";
            eliminarAppModal.bloqueNombre.classList.remove("oculto");
            eliminarAppModal.botonConfirmar.classList.remove("oculto");
            eliminarAppModal.botonConfirmar.disabled = true;
            eliminarAppModal.botonCancelar.textContent = "Cancelar";
        }
    }

    eliminarAppModal.botonAbrir.addEventListener("click", function () {
        prepararEliminarApp();
        eliminarAppModal.modal.showModal();
    });

    eliminarAppModal.campoNombre.addEventListener("input", function () {
        eliminarAppModal.botonConfirmar.disabled = normalizar(eliminarAppModal.campoNombre.value) !== normalizar(estado.aplicacionActual.nombre);
    });

    eliminarAppModal.botonCancelar.addEventListener("click", function () {
        eliminarAppModal.modal.close();
    });

    eliminarAppModal.modal.addEventListener("close", function () {
        eliminarAppModal.campoNombre.value = "";
    });

    eliminarAppModal.botonConfirmar.addEventListener("click", async function () {
        const aplicacion = estado.aplicacionActual;

        eliminarAppModal.botonConfirmar.disabled = true;
        eliminarAppModal.botonConfirmar.textContent = "Eliminando...";
        const resultado = await eliminarAplicacion(aplicacion.clientId);
        eliminarAppModal.botonConfirmar.textContent = "Eliminar aplicación";

        if (!resultado.exito) {
            if (resultado.motivo === "tiene-usuarios") {
                estado.cantidadUsuarios = resultado.cantidadUsuarios;
                prepararEliminarApp();
                mostrarError(eliminarAppModal.error, "La aplicación ahora tiene " + textoUsuarios(resultado.cantidadUsuarios) + ", así que no se eliminó.");
            } else {
                eliminarAppModal.botonConfirmar.disabled = false;
                mostrarError(eliminarAppModal.error, "No se pudo eliminar la aplicación. Intente nuevamente.");
            }
            return;
        }

        let mensaje = "Aplicación «" + aplicacion.nombre + "» eliminada.";
        if (resultado.rolesEliminados === 1) {
            mensaje = mensaje + " También se eliminó su rol.";
        } else if (resultado.rolesEliminados > 1) {
            mensaje = mensaje + " También se eliminaron sus " + resultado.rolesEliminados + " roles.";
        }
        guardarAvisoPendiente(mensaje, "exito");
        window.location.replace("apps.html");
    });
}