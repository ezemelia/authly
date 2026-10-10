import { regenerarSecret } from "../modules/api.js";
import { activarCopia } from "../modules/components.js";
import { mostrarError } from "../modules/notifications.js";
import { estado } from "./estado.js";

export function iniciarCredenciales() {
    const botonRegenerar = document.getElementById("boton-regenerar");

    const confirmacion = {
        modal: document.getElementById("modal-confirmar-regenerar"),
        texto: document.getElementById("texto-confirmar-regenerar"),
        error: document.getElementById("error-regenerar"),
        botonConfirmar: document.getElementById("boton-confirmar-regenerar"),
        botonCancelar: document.getElementById("boton-cancelar-regenerar")
    };

    const secretNuevo = {
        modal: document.getElementById("modal-secret"),
        valor: document.getElementById("valor-secret-nuevo"),
        botonCopiar: document.getElementById("boton-copiar-secret"),
        botonEntendido: document.getElementById("boton-entendido")
    };

    botonRegenerar.addEventListener("click", function () {
        confirmacion.texto.textContent = "¿Desea regenerar el client secret de " + estado.aplicacionActual.nombre + "?";
        confirmacion.modal.showModal();
    });

    confirmacion.botonCancelar.addEventListener("click", function () {
        confirmacion.modal.close();
    });

    confirmacion.modal.addEventListener("close", function () {
        confirmacion.error.classList.add("oculto");
    });

    confirmacion.botonConfirmar.addEventListener("click", async function () {
        confirmacion.botonConfirmar.disabled = true;
        confirmacion.botonConfirmar.textContent = "Regenerando...";
        const resultado = await regenerarSecret(estado.aplicacionActual.clientId);
        confirmacion.botonConfirmar.disabled = false;
        confirmacion.botonConfirmar.textContent = "Regenerar";

        if (!resultado.exito) {
            mostrarError(confirmacion.error, "No se pudo regenerar el client secret. Intente nuevamente.");
            return;
        }

        confirmacion.modal.close();
        secretNuevo.valor.textContent = resultado.secret;
        secretNuevo.modal.showModal();
    });

    activarCopia(secretNuevo.botonCopiar, function () {
        return secretNuevo.valor.textContent;
    });

    secretNuevo.modal.addEventListener("cancel", function (evento) {
        evento.preventDefault();
    });

    secretNuevo.modal.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") {
            evento.preventDefault();
        }
    });

    secretNuevo.botonEntendido.addEventListener("click", function () {
        secretNuevo.modal.close();
    });

    secretNuevo.modal.addEventListener("close", function () {
        secretNuevo.valor.textContent = "";
    });
}