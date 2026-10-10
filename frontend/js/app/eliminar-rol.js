import { eliminarRol } from "../modules/api.js";
import { mostrarError, mostrarToast } from "../modules/notifications.js";
import { textoUsuarios } from "../modules/utils.js";
import { estado } from "./estado.js";
import { cargarRoles } from "./roles.js";

let eliminarRolModal = null;
let rolAEliminar = null;

export function abrirEliminarRol(rol) {
    rolAEliminar = rol;
    eliminarRolModal.error.classList.add("oculto");

    if (rol.cantidadUsuarios > 0) {
        eliminarRolModal.titulo.textContent = "No se puede eliminar el rol";
        let verbo = "lo tienen";
        let consejo = "Cámbieles el rol o elimínelos";
        if (rol.cantidadUsuarios === 1) {
            verbo = "lo tiene";
            consejo = "Cámbiele el rol o elimínelo";
        }
        eliminarRolModal.aviso.textContent = "El rol «" + rol.nombre + "» " + verbo + " asignado " + textoUsuarios(rol.cantidadUsuarios) + ". " + consejo + " desde la pestaña «Usuarios», y luego vuelva a intentarlo.";
        eliminarRolModal.botonConfirmar.classList.add("oculto");
        eliminarRolModal.botonCancelar.textContent = "Entendido";
    } else {
        eliminarRolModal.titulo.textContent = "Eliminar rol";
        let texto = "Se eliminarán el rol «" + rol.nombre + "» y sus permisos.";
        if (rol.porDefecto) {
            texto = texto + " Es el rol por defecto: la aplicación quedará sin ninguno y no podrá registrar usuarios nuevos hasta que marque otro.";
        }
        eliminarRolModal.aviso.textContent = texto;
        eliminarRolModal.botonConfirmar.classList.remove("oculto");
        eliminarRolModal.botonCancelar.textContent = "Cancelar";
    }

    eliminarRolModal.modal.showModal();
}

export function iniciarEliminarRol() {
    eliminarRolModal = {
        modal: document.getElementById("modal-eliminar-rol"),
        titulo: document.getElementById("titulo-eliminar-rol"),
        aviso: document.getElementById("aviso-eliminar-rol"),
        error: document.getElementById("error-eliminar-rol"),
        botonConfirmar: document.getElementById("boton-confirmar-eliminar"),
        botonCancelar: document.getElementById("boton-cancelar-eliminar")
    };

    eliminarRolModal.botonCancelar.addEventListener("click", function () {
        eliminarRolModal.modal.close();
    });

    eliminarRolModal.modal.addEventListener("close", function () {
        rolAEliminar = null;
    });

    eliminarRolModal.botonConfirmar.addEventListener("click", async function () {
        const rol = rolAEliminar;

        eliminarRolModal.botonConfirmar.disabled = true;
        eliminarRolModal.botonConfirmar.textContent = "Eliminando...";
        const resultado = await eliminarRol(estado.aplicacionActual.clientId, rol.id);
        eliminarRolModal.botonConfirmar.disabled = false;
        eliminarRolModal.botonConfirmar.textContent = "Eliminar";

        if (!resultado.exito) {
            if (resultado.motivo === "tiene-usuarios") {
                mostrarError(eliminarRolModal.error, "El rol ahora tiene " + textoUsuarios(resultado.cantidadUsuarios) + ", así que no se eliminó. Actualice la lista.");
                cargarRoles();
            } else {
                mostrarError(eliminarRolModal.error, "No se pudo eliminar el rol. Intente nuevamente.");
            }
            return;
        }

        eliminarRolModal.modal.close();
        mostrarToast("Rol «" + rol.nombre + "» eliminado.", "exito");
        cargarRoles();
    });
}