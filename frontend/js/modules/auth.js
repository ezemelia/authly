import { guardarAvisoPendiente } from "./notifications.js";

let expirando = false;

export function guardarSesion(token, email, organizacion) {
    localStorage.setItem("token", token);
    localStorage.setItem("email", email);
    localStorage.setItem("organizacion", organizacion);
}

export function obtenerToken() {
    return localStorage.getItem("token");
}

export function obtenerEmail() {
    return localStorage.getItem("email");
}

export function obtenerOrganizacion() {
    return localStorage.getItem("organizacion");
}

function borrarSesion() {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    localStorage.removeItem("organizacion");
}

export function exigirSesion() {
    if (obtenerToken() === null) {
        window.location.replace("login.html");
    }
}

export function cerrarSesion() {
    borrarSesion();
    window.location.replace("login.html");
}

export function expirarSesion() {
    if (expirando) {
        return;
    }
    expirando = true;
    borrarSesion();
    guardarAvisoPendiente("Su sesión expiró. Inicie sesión de nuevo.", "error");
    window.location.replace("login.html");
}
  
