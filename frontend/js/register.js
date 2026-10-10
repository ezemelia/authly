import { validarCampo, validarEmail, validarPass, validarConfirmacion, validarCuit, validarCodigo} from "./modules/validators.js";
import { iniciarTema } from "./modules/theme.js";
import { pedirCodigo, confirmarCodigo } from "./modules/api.js";
import { mostrarError } from "./modules/notifications.js";
import { activarOjo, irAlPaso } from "./modules/components.js";

iniciarTema();

const indicadores = {
    datos: document.getElementById("indicador-datos"),
    codigo: document.getElementById("indicador-codigo"),
    confirmacion: document.getElementById("indicador-confirmacion")
};

const pasos = {
    datos: document.getElementById("paso-datos"),
    codigo: document.getElementById("paso-codigo"),
    confirmacion: document.getElementById("paso-confirmacion")
};

const botones = {
    continuar: document.getElementById("siguiente-paso"),
    verificar: document.getElementById("boton-verificacion"),
    reenviar: document.getElementById("boton-reenvio"),
    ojoPass: document.getElementById("boton-ojo-pass"),
    ojoConfirmacion: document.getElementById("boton-ojo-confirmar")
};

const campos = {
    nombre: document.getElementById("nombre-admin"),
    apellido: document.getElementById("apellido-admin"),
    email: document.getElementById("email-admin"),
    pass: document.getElementById("pass-admin"),
    confirmacion: document.getElementById("confirmar-admin"),
    nombreOrg: document.getElementById("nombre-org"),
    cuit: document.getElementById("cuit-org"),
    codigo: document.getElementById("codigo-verificacion")
};

const errores = {
    nombre: document.getElementById("error-nombre"),
    apellido: document.getElementById("error-apellido"),
    email: document.getElementById("error-email"),
    pass: document.getElementById("error-pass"),
    confirmacion: document.getElementById("error-confirmar"),
    nombreOrg: document.getElementById("error-nombre-org"),
    cuit: document.getElementById("error-cuit-org"),
    codigo: document.getElementById("error-codigo-verificacion"),
    general: document.getElementById("error-general")
};

const formularios = {
    datos: document.getElementById("formulario-registro"),
    codigo: document.getElementById("formulario-codigo")
};

const avisoReenvio = document.getElementById("aviso-reenvio");

formularios.datos.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    const resultados = [
        validarCampo(campos.nombre, errores.nombre),
        validarCampo(campos.apellido, errores.apellido), 
        validarEmail(campos.email, errores.email), 
        validarPass(campos.pass, errores.pass), 
        validarConfirmacion(campos.confirmacion, campos.pass, errores.confirmacion),
        validarCampo(campos.nombreOrg, errores.nombreOrg), 
        validarCuit(campos.cuit, errores.cuit)
    ];
    if (resultados.includes(false)) {
        return;
    }

    errores.general.classList.add("oculto");
    botones.continuar.disabled = true;
    botones.continuar.textContent = "Enviando...";
    const respuesta = await pedirCodigo({ email: campos.email.value.trim().toLowerCase(), cuit: campos.cuit.value.trim() });
    botones.continuar.disabled = false;
    botones.continuar.textContent = "Continuar";

    if (!respuesta.exito) {
        if (respuesta.campo === "email") {
            mostrarError(errores.email, respuesta.mensaje);
        }
        if (respuesta.campo === "cuit") {
            mostrarError(errores.cuit, respuesta.mensaje);
        }
        if (respuesta.campo === "general") {
            mostrarError(errores.general, respuesta.mensaje);
        }
    return;
    }

    irAlPaso(pasos, indicadores, "datos", "codigo");
});

activarOjo(botones.ojoPass, campos.pass);
activarOjo(botones.ojoConfirmacion, campos.confirmacion);

formularios.codigo.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    if (validarCodigo(campos.codigo, errores.codigo)) {
        avisoReenvio.classList.add("oculto");
        const datos = {
            codigo: campos.codigo.value.trim(),
            nombre: campos.nombre.value.trim(),
            apellido: campos.apellido.value.trim(),
            email: campos.email.value.trim().toLowerCase(),
            password: campos.pass.value,
            nombreOrg: campos.nombreOrg.value.trim(),
            cuit: campos.cuit.value.trim()
        };
        botones.verificar.disabled = true;
        botones.verificar.textContent = "Verificando...";
        const respuesta = await confirmarCodigo(datos);
        botones.verificar.disabled = false;
        botones.verificar.textContent = "Verificar";
        if (!respuesta.exito) {
            if (respuesta.reinicio) {
                irAlPaso(pasos, indicadores, "codigo", "datos");
                if (respuesta.campo === "email") {
                    mostrarError(errores.email, respuesta.mensaje);
                } else if (respuesta.campo === "cuit") {
                    mostrarError(errores.cuit, respuesta.mensaje);
                } else {
                    mostrarError(errores.general, respuesta.mensaje);
                }
                campos.codigo.value = "";
                errores.codigo.classList.add("oculto");
                return;
            }
            mostrarError(errores.codigo, respuesta.mensaje);
            return;
        }
        irAlPaso(pasos, indicadores, "codigo", "confirmacion");
    }
});

botones.reenviar.addEventListener("click", async function() {
    botones.reenviar.disabled = true;
    botones.reenviar.textContent = "Reenviando...";
    const respuesta = await pedirCodigo({ email: campos.email.value.trim().toLowerCase(), cuit: campos.cuit.value.trim()});
    botones.reenviar.disabled = false;
    botones.reenviar.textContent = "Reenviar código";
    if (!respuesta.exito) {
        mostrarError(errores.codigo, respuesta.mensaje);
        avisoReenvio.classList.add("oculto");
        return;
    }
    errores.codigo.classList.add("oculto");
    avisoReenvio.textContent = "Le enviamos un código nuevo. Revise su correo.";
    avisoReenvio.classList.remove("oculto");
});



