import { editarAplicacion } from "../modules/api.js";
import { mostrarError } from "../modules/notifications.js";
import { validarCampo } from "../modules/validators.js";
import { estado } from "./estado.js";
import { mostrarDatos } from "./aplicacion.js";

export function iniciarEditarApp() {
    const editar = {
        modal: document.getElementById("modal-editar-app"),
        formulario: document.getElementById("formulario-editar-app"),
        nombre: document.getElementById("nombre-editar"),
        descripcion: document.getElementById("descripcion-editar"),
        error: document.getElementById("error-nombre-editar"),
        botonAbrir: document.getElementById("boton-editar"),
        botonCancelar: document.getElementById("boton-cancelar-editar"),
        botonGuardar: document.getElementById("boton-guardar-editar")
    };

    editar.botonAbrir.addEventListener("click", function () {
        editar.nombre.value = estado.aplicacionActual.nombre;
        editar.descripcion.value = estado.aplicacionActual.descripcion;
        editar.modal.showModal();
    });

    editar.botonCancelar.addEventListener("click", function () {
        editar.modal.close();
    });

    editar.modal.addEventListener("close", function () {
        editar.error.classList.add("oculto");
    });

    editar.formulario.addEventListener("submit", async function (evento) {
        evento.preventDefault();
        editar.error.textContent = "Campo incompleto. Ingrese el nombre de la aplicación.";
        if (!validarCampo(editar.nombre, editar.error)) {
            return;
        }

        editar.botonGuardar.disabled = true;
        editar.botonGuardar.textContent = "Guardando...";
        const resultado = await editarAplicacion(estado.aplicacionActual.clientId, {nombre: editar.nombre.value, descripcion: editar.descripcion.value});
        editar.botonGuardar.disabled = false;
        editar.botonGuardar.textContent = "Guardar";

        if (!resultado.exito) {
            if (resultado.campo === "nombre") {
                mostrarError(editar.error, resultado.mensaje);
            } else {
                mostrarError(editar.error, "No se pudieron guardar los cambios. Intente nuevamente.");
            }
            return;
        }

        estado.aplicacionActual = resultado.aplicacion;
        mostrarDatos(estado.aplicacionActual);
        editar.modal.close();
    });
}