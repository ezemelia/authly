import { validarCampo, validarEmail} from "./modules/validators.js";
import { iniciarTema } from "./modules/theme.js";
import { activarOjo } from "./modules/components.js";
import { iniciarSesion } from "./modules/api.js";
import { guardarSesion } from "./modules/auth.js";
import { mostrarError, mostrarAvisoPendiente } from "./modules/notifications.js";

iniciarTema();
mostrarAvisoPendiente();

const campos = {
    email: document.getElementById("email-admin"),
    pass: document.getElementById("pass-admin")
};

const errores = {
    email: document.getElementById("error-email"),
    pass: document.getElementById("error-pass"),
    general: document.getElementById("error-general")
};

const botones = {
    ingreso: document.getElementById("boton-ingreso"),
    ojoPass: document.getElementById("boton-ojo-pass")
};

const formulario = document.getElementById("formulario-ingreso");

activarOjo(botones.ojoPass, campos.pass);

formulario.addEventListener("submit", async function(evento) {
    evento.preventDefault();
    const resultados = [
        validarEmail(campos.email, errores.email),
        validarCampo(campos.pass, errores.pass)];
    if (resultados.includes(false)) {
        return;
    }
    errores.general.classList.add("oculto");
    botones.ingreso.disabled = true;
    botones.ingreso.textContent = "Ingresando...";
    const respuesta = await iniciarSesion({email: campos.email.value.trim().toLowerCase(), password: campos.pass.value});
    botones.ingreso.disabled = false;
    botones.ingreso.textContent = "Iniciar sesión";
    if (!respuesta.exito) {
        mostrarError(errores.general, "Credenciales inválidas.");
        return;
    }  
    guardarSesion(respuesta.token, respuesta.email, respuesta.organizacion);
    window.location.href = "apps.html"
});