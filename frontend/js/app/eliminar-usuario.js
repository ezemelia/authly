import { eliminarUsuario } from "../modules/api.js";
import { mostrarError, mostrarToast } from "../modules/notifications.js";
import { estado } from "./estado.js";
import { cargarRoles } from "./roles.js";
import { cargarUsuarios } from "./usuarios.js";

let eliminarUsuarioModal = null;
let usuarioAEliminar = null;

export function abrirEliminarUsuario(usuario) {
    usuarioAEliminar = usuario;
    eliminarUsuarioModal.error.classList.add("oculto");
    eliminarUsuarioModal.nombre.textContent = usuario.nombre + " " + usuario.apellido;
    eliminarUsuarioModal.email.textContent = usuario.email;
    eliminarUsuarioModal.roles.textContent = usuario.roles.map(function (rol) {
        return rol.nombre;
    }).join(", ");
    eliminarUsuarioModal.modal.showModal();
}

export function iniciarEliminarUsuario() {
    eliminarUsuarioModal = {
        modal: document.getElementById("modal-eliminar-usuario"),
        nombre: document.getElementById("nombre-eliminar-usuario"),
        email: document.getElementById("email-eliminar-usuario"),
        roles: document.getElementById("roles-eliminar-usuario"),
        error: document.getElementById("error-eliminar-usuario"),
        botonConfirmar: document.getElementById("boton-confirmar-eliminar-usuario"),
        botonCancelar: document.getElementById("boton-cancelar-eliminar-usuario")
    };

    eliminarUsuarioModal.botonCancelar.addEventListener("click", function () {
        eliminarUsuarioModal.modal.close();
    });

    eliminarUsuarioModal.modal.addEventListener("close", function () {
        usuarioAEliminar = null;
    });

    eliminarUsuarioModal.botonConfirmar.addEventListener("click", async function () {
        const usuario = usuarioAEliminar;

        eliminarUsuarioModal.botonConfirmar.disabled = true;
        eliminarUsuarioModal.botonConfirmar.textContent = "Eliminando...";
        const resultado = await eliminarUsuario(estado.aplicacionActual.clientId, usuario.id);
        eliminarUsuarioModal.botonConfirmar.disabled = false;
        eliminarUsuarioModal.botonConfirmar.textContent = "Eliminar usuario";

        if (!resultado.exito) {
            if (resultado.motivo === "usuario-inexistente") {
                eliminarUsuarioModal.modal.close();
                mostrarToast("El usuario «" + usuario.nombre + " " + usuario.apellido + "» ya no existe. Se actualizó la lista.", "error");
                cargarUsuarios();
                cargarRoles();
            } else {
                mostrarError(eliminarUsuarioModal.error, "No se pudo eliminar el usuario. Intente nuevamente.");
            }
            return;
        }

        eliminarUsuarioModal.modal.close();
        mostrarToast("Usuario «" + usuario.nombre + " " + usuario.apellido + "» eliminado.", "exito");
        cargarUsuarios();
        cargarRoles();
    });
}