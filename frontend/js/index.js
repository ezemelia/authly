import { obtenerToken } from "./modules/auth.js";

const tokenObtenido = obtenerToken();

if (tokenObtenido !== null) {
    window.location.replace("apps.html");
} else { 
    window.location.replace("login.html");
}