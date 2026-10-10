import { editarUsuario } from "../modules/api.js";
import { mostrarError, mostrarToast } from "../modules/notifications.js";
import { validarCampo } from "../modules/validators.js";
import { estado } from "./estado.js";
import { cargarRoles } from "./roles.js";
import { cargarUsuarios } from "./usuarios.js";

let editarUsuarioModal = null;
let usuarioEnEdicion = null;

function crearCasillaRol(rol, marcado) {
    const contenedor = document.createElement("div");
    contenedor.classList.add("casilla-rol");

    const casilla = document.createElement("input");
    casilla.type = "checkbox";
    casilla.id = "casilla-rol-" + rol.id;
    casilla.value = rol.id;
    casilla.checked = marcado;

    const etiqueta = document.createElement("label");
    etiqueta.setAttribute("for", casilla.id);
    etiqueta.textContent = rol.nombre;
    if (rol.porDefecto) {
        const predeterminado = document.createElement("span");
        predeterminado.classList.add("etiqueta-predeterminado");
        predeterminado.textContent = "Predeterminado";
        etiqueta.append(predeterminado);
    }
    if (rol.descripcion !== "") {
        const descripcion = document.createElement("span");
        descripcion.classList.add("descripcion");
        descripcion.textContent = rol.descripcion;
        etiqueta.append(descripcion);
    }

    contenedor.append(casilla, etiqueta);
    return contenedor;
}

function rolesMarcados() {
    const elegidos = [];
    const casillas = editarUsuarioModal.listaRoles.querySelectorAll("input[type='checkbox']");
    for (const casilla of casillas) {
        if (casilla.checked) {
            elegidos.push(casilla.value);
        }
    }
    return elegidos;
}

function nombreDelRol(rolId) {
    const rol = estado.roles.find(function (candidato) {
        return candidato.id === rolId;
    });
    if (rol === undefined) {
        return null;
    }
    return rol.nombre;
}

export function abrirEditarUsuario(usuario) {
    usuarioEnEdicion = usuario;
    editarUsuarioModal.email.textContent = usuario.email;
    editarUsuarioModal.nombre.value = usuario.nombre;
    editarUsuarioModal.apellido.value = usuario.apellido;

    const idsDelUsuario = usuario.roles.map(function (rol) {
        return rol.id;
    });
    editarUsuarioModal.listaRoles.replaceChildren();
    for (const rol of estado.roles) {
        editarUsuarioModal.listaRoles.append(crearCasillaRol(rol, idsDelUsuario.includes(rol.id)));
    }

    editarUsuarioModal.modal.showModal();
}

export function iniciarEditarUsuario() {
    editarUsuarioModal = {
        modal: document.getElementById("modal-editar-usuario"),
        formulario: document.getElementById("formulario-editar-usuario"),
        email: document.getElementById("email-editar-usuario"),
        nombre: document.getElementById("nombre-usuario"),
        errorNombre: document.getElementById("error-nombre-usuario"),
        apellido: document.getElementById("apellido-usuario"),
        errorApellido: document.getElementById("error-apellido-usuario"),
        listaRoles: document.getElementById("lista-roles-usuario"),
        errorRoles: document.getElementById("error-roles-usuario"),
        errorGeneral: document.getElementById("error-general-usuario"),
        botonGuardar: document.getElementById("boton-guardar-usuario"),
        botonCancelar: document.getElementById("boton-cancelar-usuario")
    };

    editarUsuarioModal.botonCancelar.addEventListener("click", function () {
        editarUsuarioModal.modal.close();
    });

    editarUsuarioModal.modal.addEventListener("close", function () {
        editarUsuarioModal.errorNombre.classList.add("oculto");
        editarUsuarioModal.errorApellido.classList.add("oculto");
        editarUsuarioModal.errorRoles.classList.add("oculto");
        editarUsuarioModal.errorGeneral.classList.add("oculto");
        editarUsuarioModal.listaRoles.replaceChildren();
        usuarioEnEdicion = null;
    });

    editarUsuarioModal.formulario.addEventListener("submit", async function (evento) {
        evento.preventDefault();
        editarUsuarioModal.errorGeneral.classList.add("oculto");
        editarUsuarioModal.errorRoles.classList.add("oculto");

        const nombreValido = validarCampo(editarUsuarioModal.nombre, editarUsuarioModal.errorNombre);
        const apellidoValido = validarCampo(editarUsuarioModal.apellido, editarUsuarioModal.errorApellido);
        const rolesElegidos = rolesMarcados();
        if (rolesElegidos.length === 0) {
            editarUsuarioModal.errorRoles.classList.remove("oculto");
        }
        if (!nombreValido || !apellidoValido || rolesElegidos.length === 0) {
            return;
        }

        const usuario = usuarioEnEdicion;
        editarUsuarioModal.botonGuardar.disabled = true;
        editarUsuarioModal.botonGuardar.textContent = "Guardando...";
        const resultado = await editarUsuario(estado.aplicacionActual.clientId, usuario.id, {
            nombre: editarUsuarioModal.nombre.value,
            apellido: editarUsuarioModal.apellido.value,
            roles: rolesElegidos
        });
        editarUsuarioModal.botonGuardar.disabled = false;
        editarUsuarioModal.botonGuardar.textContent = "Guardar";

        if (!resultado.exito) {
            if (resultado.campo === "nombre") {
                mostrarError(editarUsuarioModal.errorNombre, "Campo incompleto. Ingrese el nombre.");
            } else if (resultado.campo === "apellido") {
                mostrarError(editarUsuarioModal.errorApellido, "Campo incompleto. Ingrese el apellido.");
            } else if (resultado.campo === "roles") {
                mostrarError(editarUsuarioModal.errorRoles, "El usuario debe tener al menos un rol.");
            } else if (resultado.motivo === "usuario-inexistente") {
                editarUsuarioModal.modal.close();
                mostrarToast("El usuario «" + usuario.nombre + " " + usuario.apellido + "» ya no existe. Se actualizó la lista.", "error");
                cargarUsuarios();
            } else if (resultado.motivo === "rol-inexistente") {
                const nombreRol = nombreDelRol(resultado.rolId);
                const cual = nombreRol === null ? "Uno de los roles" : "El rol «" + nombreRol + "»";
                editarUsuarioModal.modal.close();
                mostrarToast(cual + " ya no existe. Se actualizaron los roles.", "error");
                cargarRoles();
                cargarUsuarios();
            } else {
                mostrarError(editarUsuarioModal.errorGeneral, "No se pudieron guardar los cambios. Intente nuevamente.");
            }
            return;
        }

        editarUsuarioModal.modal.close();
        mostrarToast("Usuario «" + resultado.usuario.nombre + " " + resultado.usuario.apellido + "» guardado.", "exito");
        cargarUsuarios();
        cargarRoles();
    });
}