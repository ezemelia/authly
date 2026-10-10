export function obtenerParametro(nombre) {
    return new URLSearchParams(window.location.search).get(nombre);
}

export function normalizar(texto) {
    return texto.trim().toLowerCase();
}

export function textoUsuarios(cantidad) {
    if (cantidad === 1) {
        return "1 usuario";
    }
    return cantidad + " usuarios";
}