import { iniciarTema } from "./modules/theme.js";
import { activarOjo, irAlPaso } from "./modules/components.js";
import { validarEmail, validarCodigo, validarPass, validarConfirmacion } from "./modules/validators.js";
import { pedirCodigoRecuperacion, cambiarPassword } from "./modules/api.js";
import { mostrarError } from "./modules/notifications.js";

iniciarTema();

const indicadores = {
    correo: document.getElementById("indicador-email"),
    codigo: document.getElementById("indicador-cambio-pass"),
    confirmacion: document.getElementById("indicador-confirmacion")
};

const pasos = {
    correo: document.getElementById("paso-datos"),
    codigo: document.getElementById("paso-codigo"),
    confirmacion: document.getElementById("paso-confirmacion")
};

const formularios = {
    correo: document.getElementById("formulario-correo"),
    codigo: document.getElementById("formulario-codigo")
};

const campos = {
    email: document.getElementById("email-admin"),
    pass: document.getElementById("pass-admin"),
    confirmacion: document.getElementById("confirmar-admin"),
    codigo: document.getElementById("codigo-verificacion")
};

const errores = {
    email: document.getElementById("error-email"),
    pass: document.getElementById("error-pass"),
    confirmacion: document.getElementById("error-confirmar"),
    codigo: document.getElementById("error-codigo-verificacion")
};

const botones = {
    envio: document.getElementById("boton-envio"),
    cambio: document.getElementById("boton-cambio"),
    nuevoCodigo: document.getElementById("boton-nuevo-codigo"),
    ojoPass: document.getElementById("boton-ojo-pass"),
    ojoConfirmacion: document.getElementById("boton-ojo-confirmar")
};

activarOjo(botones.ojoPass, campos.pass);
activarOjo(botones.ojoConfirmacion, campos.confirmacion);

formularios.correo.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    if (!validarEmail(campos.email, errores.email)) { 
        return;
    }

    botones.envio.disabled = true;
    botones.envio.textContent = "Enviando...";
    await pedirCodigoRecuperacion({ email: campos.email.value.trim().toLowerCase()});
    botones.envio.disabled = false;
    botones.envio.textContent = "Enviar código";
    irAlPaso(pasos, indicadores, "correo", "codigo");
});

formularios.codigo.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    const resultados = [
        validarCodigo(campos.codigo, errores.codigo),
        validarPass(campos.pass, errores.pass),
        validarConfirmacion(campos.confirmacion, campos.pass, errores.confirmacion)
    ];
    if (resultados.includes(false)) {
        return;
    }

    botones.cambio.disabled = true;
    botones.cambio.textContent = "Cambiando...";
    const respuesta = await cambiarPassword({ email: campos.email.value.trim().toLowerCase(), codigo: campos.codigo.value.trim(), password: campos.pass.value});
    botones.cambio.disabled = false;
    botones.cambio.textContent = "Cambiar contraseña";
    if (!respuesta.exito) {
    if (respuesta.campo === "codigo") {
        mostrarError(errores.codigo, "Código inválido o vencido.");
    }
    if (respuesta.campo === "pass") {
        mostrarError(errores.pass, "La contraseña nueva debe ser distinta de la actual.");
    }
    return;
}
    irAlPaso(pasos, indicadores, "codigo", "confirmacion");

});

botones.nuevoCodigo.addEventListener("click", function() {
    irAlPaso(pasos, indicadores, "codigo", "correo");
    for (const campo of [campos.codigo, campos.pass, campos.confirmacion]) {
        campo.value = "";
    }
    for (const error of [errores.codigo, errores.pass, errores.confirmacion]) {
        error.classList.add("oculto");
    }
    if (campos.pass.type === "text") {
        botones.ojoPass.click();
    }
    if (campos.confirmacion.type === "text") {
        botones.ojoConfirmacion.click();
    }
});
