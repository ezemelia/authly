import { cerrarSesion, obtenerEmail, obtenerOrganizacion } from "./auth.js";

export function iniciarEncabezado() {
    const emailAdministrador = document.getElementById("email-administrador");
    const nombreOrganizacion = document.getElementById("nombre-organizacion");
    const botonCerrarSesion = document.getElementById("boton-cerrar-sesion");

    emailAdministrador.textContent = obtenerEmail();
    nombreOrganizacion.textContent = obtenerOrganizacion();

    botonCerrarSesion.addEventListener("click", cerrarSesion);
}