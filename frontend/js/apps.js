import { iniciarTema } from "./modules/theme.js";
import { exigirSesion } from "./modules/auth.js";
import { listarAplicaciones, crearAplicacion } from "./modules/api.js";
import { validarCampo } from "./modules/validators.js";
import { mostrarError, mostrarAvisoPendiente } from "./modules/notifications.js";
import { iniciarEncabezado } from "./modules/encabezado.js";
import { activarCopia, crearPaginador } from "./modules/components.js";
import { textoUsuarios } from "./modules/utils.js";

exigirSesion();
iniciarTema();
iniciarEncabezado();
mostrarAvisoPendiente();

const crearApp = {
    modal: document.getElementById("modal-crear-app"),
    formulario: document.getElementById("formulario-crear-app"),
    nombre: document.getElementById("nombre-app"),
    descripcion: document.getElementById("descripcion-app"),
    error: document.getElementById("error-nombre-app"),
    botonAbrir: document.getElementById("boton-crear-app"),
    botonCancelar: document.getElementById("boton-cancelar-app"),
    botonGuardar: document.getElementById("boton-guardar-app")
};

const credenciales = {
    modal: document.getElementById("modal-credenciales"),
    titulo: document.getElementById("titulo-credenciales"),
    clientId: document.getElementById("credencial-client-id"),
    secret: document.getElementById("credencial-secret"),
    botonCopiarClientId: document.getElementById("boton-copiar-client-id"),
    botonCopiarSecret: document.getElementById("boton-copiar-secret"),
    botonEntendido: document.getElementById("boton-entendido")
};

const cuerpoTablaApps = document.getElementById("cuerpo-tabla-apps");
const tablaApps = document.getElementById("tabla-apps");
const estadoVacio = document.getElementById("estado-vacio");
const estadoCarga = document.getElementById("estado-carga");

const resumenApps = document.getElementById("resumen-apps");
const navPaginador = document.getElementById("paginador-apps");

const TAMANIO = 10;
let paginaActual = 1;

const paginador = crearPaginador(navPaginador, function (pagina) {
    paginaActual = pagina;
    cargarAplicaciones();
});

function textoAplicaciones(cantidad) {
    if (cantidad === 1) {
        return "1 aplicación";
    }
    return cantidad + " aplicaciones";
}

function crearFila(aplicacion) {

    const fila = document.createElement("tr");
    const celdaTitulo = document.createElement("td");
    const enlace = document.createElement("a");

    enlace.textContent = aplicacion.nombre;
    enlace.href = "app.html?id=" + aplicacion.clientId;
    celdaTitulo.append(enlace);

    if (aplicacion.descripcion !== "") {
        const descripcion = document.createElement("span");
        descripcion.classList.add("descripcion");
        descripcion.textContent = aplicacion.descripcion;
        celdaTitulo.append(descripcion);
    }

    const celdaClientId = document.createElement("td");
    celdaClientId.dataset.etiqueta = "Client ID";
    const textoClientId = document.createElement("span");
    textoClientId.classList.add("client-id");
    textoClientId.textContent = aplicacion.clientId;
    const botonCopiar = document.createElement("button");
    botonCopiar.type = "button";
    botonCopiar.textContent = "Copiar";
    botonCopiar.classList.add("boton-secundario", "boton-chico");
    activarCopia(botonCopiar, function () {
        return aplicacion.clientId;
    });
    celdaClientId.append(textoClientId, botonCopiar);
    const celdaUsuarios = document.createElement("td");
    celdaUsuarios.dataset.etiqueta = "Usuarios";
    celdaUsuarios.textContent = aplicacion.cantidadUsuarios;
    fila.append(celdaTitulo, celdaClientId, celdaUsuarios);

    return fila;
}

function mostrarAplicaciones(aplicaciones, total, totalUsuarios) {
    estadoCarga.classList.add("oculto");
    cuerpoTablaApps.replaceChildren();
    for (const aplicacion of aplicaciones) {
        cuerpoTablaApps.append(crearFila(aplicacion));
    }
    if (total === 0) {
        tablaApps.classList.add("oculto");
        resumenApps.classList.add("oculto");
        estadoVacio.classList.remove("oculto");
    } else {
        tablaApps.classList.remove("oculto");
        resumenApps.textContent = textoAplicaciones(total) + " · " + textoUsuarios(totalUsuarios) + " en total";
        resumenApps.classList.remove("oculto");
        estadoVacio.classList.add("oculto");
    }
    paginador.mostrar(paginaActual, total, TAMANIO);
}

async function cargarAplicaciones() {
    estadoCarga.textContent = "Cargando aplicaciones...";
    estadoCarga.classList.remove("oculto");
    tablaApps.classList.add("oculto");
    resumenApps.classList.add("oculto");
    estadoVacio.classList.add("oculto");
    navPaginador.classList.add("oculto");

    const respuesta = await listarAplicaciones({pagina: paginaActual, tamanio: TAMANIO});
    if (!respuesta.exito) {
        estadoCarga.textContent = "No se pudieron cargar las aplicaciones. Recargue la página.";
        return;
    }

    const ultimaPagina = Math.max(1, Math.ceil(respuesta.total / TAMANIO));
    if (paginaActual > ultimaPagina) {
        paginaActual = ultimaPagina;
        await cargarAplicaciones();
        return;
    }

    mostrarAplicaciones(respuesta.aplicaciones, respuesta.total, respuesta.totalUsuarios);
}

function mostrarCredenciales(clientId, secret) {
    credenciales.clientId.textContent = clientId;
    credenciales.secret.textContent = secret;
    credenciales.modal.showModal();
}

crearApp.botonAbrir.addEventListener("click", function() {
    crearApp.modal.showModal();
});

crearApp.botonCancelar.addEventListener("click", function() {
    crearApp.modal.close();
});

crearApp.modal.addEventListener("close", function() {
    crearApp.formulario.reset();
    crearApp.error.classList.add("oculto");
});

crearApp.formulario.addEventListener("submit", async function(evento) {
    evento.preventDefault();
    crearApp.error.textContent = "Campo incompleto. Ingrese el nombre de la aplicación.";
    if (!validarCampo(crearApp.nombre, crearApp.error)) {
        return;
    }

    crearApp.botonGuardar.disabled = true;
    crearApp.botonGuardar.textContent = "Creando...";
    const resultado = await crearAplicacion({nombre: crearApp.nombre.value, descripcion: crearApp.descripcion.value});
    crearApp.botonGuardar.disabled = false;
    crearApp.botonGuardar.textContent = "Crear";

    if (!resultado.exito) {
        if (resultado.campo === "nombre") {
            mostrarError(crearApp.error, resultado.mensaje);
        } else {
            mostrarError(crearApp.error, "No se pudo crear la aplicación. Intente nuevamente.");
        }
        return;
    }

    crearApp.modal.close();
    mostrarCredenciales(resultado.aplicacion.clientId, resultado.secret);
    cargarAplicaciones();
});

activarCopia(credenciales.botonCopiarClientId, function () {
    return credenciales.clientId.textContent;
});

activarCopia(credenciales.botonCopiarSecret, function () {
    return credenciales.secret.textContent;
});

credenciales.modal.addEventListener("cancel", function (evento) {
    evento.preventDefault();
});

credenciales.modal.addEventListener("keydown", function (evento) {
    if (evento.key === "Escape") {
        evento.preventDefault();
    }
});

credenciales.botonEntendido.addEventListener("click", function () {
    credenciales.modal.close();
});

credenciales.modal.addEventListener("close", function () {
    credenciales.clientId.textContent = "";
    credenciales.secret.textContent = "";
});

cargarAplicaciones();

