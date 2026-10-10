import { crearRol, editarRol } from "../modules/api.js";
import { mostrarError, mostrarToast } from "../modules/notifications.js";
import { normalizar } from "../modules/utils.js";
import { validarCampo } from "../modules/validators.js";
import { estado } from "./estado.js";
import { cargarRoles } from "./roles.js";
import { marcarUsuariosDesactualizados } from "./usuarios.js";

let formularioRol = null;
let confirmacionDefecto = null;
let rolEnEdicion = null;
let datosPendientes = null;

function mensajeRol(rol, accion, anterior) {
    let mensaje = "Rol «" + rol.nombre + "» " + accion + ".";
    if (anterior !== null) {
        mensaje = mensaje + " El rol por defecto anterior era «" + anterior + "».";
    }
    return mensaje;
}

function crearFilaPermiso(permiso) {
    const fila = document.createElement("div");
    fila.classList.add("fila-permiso");

    const campos = document.createElement("div");
    campos.classList.add("campos-permiso");

    const recurso = document.createElement("input");
    recurso.type = "text";
    recurso.placeholder = "Recurso (por ejemplo, facturas)";
    recurso.setAttribute("aria-label", "Recurso del permiso");
    recurso.classList.add("campo-recurso");

    const accion = document.createElement("input");
    accion.type = "text";
    accion.placeholder = "Acción (por ejemplo, leer)";
    accion.setAttribute("aria-label", "Acción del permiso");
    accion.classList.add("campo-accion");
    accion.setAttribute("list", "acciones-sugeridas");

    if (permiso !== undefined) {
        recurso.value = permiso.recurso;
        accion.value = permiso.accion;
    }

    const quitar = document.createElement("button");
    quitar.type = "button";
    quitar.textContent = "×";
    quitar.classList.add("boton-quitar-permiso");
    quitar.setAttribute("aria-label", "Quitar este permiso");
    quitar.addEventListener("click", function () {
        fila.remove();
    });

    const error = document.createElement("p");
    error.classList.add("mensaje-error", "oculto", "error-permiso");

    campos.append(recurso, accion, quitar);
    fila.append(campos, error);
    return fila;
}

export function abrirFormularioRol(rol) {
    if (rol === undefined) {
        rolEnEdicion = null;
        formularioRol.titulo.textContent = "Crear rol";
        formularioRol.botonGuardar.textContent = "Crear";
    } else {
        rolEnEdicion = rol;
        formularioRol.titulo.textContent = "Editar rol";
        formularioRol.botonGuardar.textContent = "Guardar";
        formularioRol.nombre.value = rol.nombre;
        formularioRol.descripcion.value = rol.descripcion;
        formularioRol.porDefecto.checked = rol.porDefecto;
        for (const permiso of rol.permisos) {
            formularioRol.listaPermisos.append(crearFilaPermiso(permiso));
        }
    }
    formularioRol.modal.showModal();
}

function validarPermisos() {
    const filas = formularioRol.listaPermisos.querySelectorAll(".fila-permiso");
    const vistos = [];
    const permisos = [];
    let valido = true;

    for (const fila of filas) {
        const recurso = normalizar(fila.querySelector(".campo-recurso").value);
        const accion = normalizar(fila.querySelector(".campo-accion").value);
        const error = fila.querySelector(".error-permiso");
        error.classList.add("oculto");

        if (recurso === "" || accion === "") {
            mostrarError(error, "Complete el recurso y la acción, o quite este permiso.");
            valido = false;
            continue;
        }

        const clave = recurso + "\n" + accion;
        if (vistos.includes(clave)) {
            mostrarError(error, "Este permiso está repetido.");
            valido = false;
            continue;
        }

        vistos.push(clave);
        permisos.push({recurso, accion});
    }

    if (valido) {
        return permisos;
    }
    return null;
}

async function guardarRol(datos) {
    const editando = rolEnEdicion !== null;
    const textoBoton = formularioRol.botonGuardar.textContent;

    formularioRol.botonGuardar.disabled = true;
    formularioRol.botonGuardar.textContent = editando ? "Guardando..." : "Creando...";

    let resultado;
    if (editando) {
        resultado = await editarRol(estado.aplicacionActual.clientId, rolEnEdicion.id, datos);
    } else {
        resultado = await crearRol(estado.aplicacionActual.clientId, datos);
    }

    formularioRol.botonGuardar.disabled = false;
    formularioRol.botonGuardar.textContent = textoBoton;

    if (!resultado.exito) {
        if (resultado.campo === "nombre") {
            mostrarError(formularioRol.errorNombre, resultado.mensaje);
        } else if (editando) {
            mostrarError(formularioRol.errorGeneral, "No se pudieron guardar los cambios. Intente nuevamente.");
        } else {
            mostrarError(formularioRol.errorGeneral, "No se pudo crear el rol. Intente nuevamente.");
        }
        return;
    }

    formularioRol.modal.close();
    mostrarToast(mensajeRol(resultado.rol, editando ? "guardado" : "creado", resultado.rolPorDefectoAnterior), "exito");
    cargarRoles();
    if (editando) {
        marcarUsuariosDesactualizados();
    }
}

export function iniciarFormularioRol() {
    formularioRol = {
        modal: document.getElementById("modal-rol"),
        formulario: document.getElementById("formulario-rol"),
        titulo: document.getElementById("titulo-modal-rol"),
        nombre: document.getElementById("nombre-rol"),
        descripcion: document.getElementById("descripcion-rol"),
        errorNombre: document.getElementById("error-nombre-rol"),
        listaPermisos: document.getElementById("lista-permisos"),
        errorPermisos: document.getElementById("error-permisos"),
        botonAgregarPermiso: document.getElementById("boton-agregar-permiso"),
        porDefecto: document.getElementById("rol-por-defecto"),
        errorGeneral: document.getElementById("error-general-rol"),
        botonGuardar: document.getElementById("boton-guardar-rol"),
        botonCancelar: document.getElementById("boton-cancelar-rol")
    };

    confirmacionDefecto = {
        modal: document.getElementById("modal-confirmar-sin-defecto"),
        texto: document.getElementById("texto-confirmar-sin-defecto"),
        botonConfirmar: document.getElementById("boton-confirmar-sin-defecto"),
        botonVolver: document.getElementById("boton-volver-formulario")
    };

    const botonCrearRol = document.getElementById("boton-crear-rol");

    botonCrearRol.addEventListener("click", function () {
        abrirFormularioRol();
    });

    formularioRol.botonCancelar.addEventListener("click", function () {
        formularioRol.modal.close();
    });

    formularioRol.modal.addEventListener("close", function () {
        formularioRol.formulario.reset();
        formularioRol.listaPermisos.replaceChildren();
        formularioRol.errorNombre.classList.add("oculto");
        formularioRol.errorPermisos.classList.add("oculto");
        formularioRol.errorGeneral.classList.add("oculto");
        rolEnEdicion = null;
    });

    formularioRol.formulario.addEventListener("submit", async function (evento) {
        evento.preventDefault();
        formularioRol.errorNombre.textContent = "Campo incompleto. Ingrese el nombre del rol.";
        formularioRol.errorGeneral.classList.add("oculto");

        const nombreValido = validarCampo(formularioRol.nombre, formularioRol.errorNombre);
        const permisos = validarPermisos();
        if (!nombreValido || permisos === null) {
            return;
        }

        const datos = {
            nombre: formularioRol.nombre.value,
            descripcion: formularioRol.descripcion.value,
            permisos: permisos,
            porDefecto: formularioRol.porDefecto.checked
        };

        if (rolEnEdicion !== null && rolEnEdicion.porDefecto && !datos.porDefecto) {
            datosPendientes = datos;
            confirmacionDefecto.texto.textContent = "¿Desea guardar los cambios del rol «" + rolEnEdicion.nombre + "»?";
            confirmacionDefecto.modal.showModal();
            return;
        }

        await guardarRol(datos);
    });

    formularioRol.botonAgregarPermiso.addEventListener("click", function () {
        const fila = crearFilaPermiso();
        formularioRol.listaPermisos.append(fila);
        fila.querySelector(".campo-recurso").focus();
    });

    confirmacionDefecto.botonVolver.addEventListener("click", function () {
        confirmacionDefecto.modal.close();
    });

    confirmacionDefecto.botonConfirmar.addEventListener("click", async function () {
        const datos = datosPendientes;
        confirmacionDefecto.modal.close();
        await guardarRol(datos);
    });

    confirmacionDefecto.modal.addEventListener("close", function () {
        datosPendientes = null;
    });
}