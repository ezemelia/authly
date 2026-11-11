export function mostrarError(elemento, mensaje) {
    elemento.textContent = mensaje;
    elemento.classList.remove("oculto");
    // Se saca y se vuelve a poner la clase, forzando un reflow en el medio, para que
    // el temblor se repita aunque el mismo error ya estuviera mostrado antes.
    elemento.classList.remove("tiembla");
    void elemento.offsetWidth;
    elemento.classList.add("tiembla");
}

const contenedorToasts = document.createElement("div");
contenedorToasts.classList.add("contenedor-toasts");
contenedorToasts.setAttribute("role", "status");
contenedorToasts.setAttribute("aria-live", "polite");
document.body.append(contenedorToasts);

function cerrarToast(toast) {
    // Dispara la animación de salida. El elemento se saca recién cuando termina
    // (por el evento, o por la red de seguridad del setTimeout si la animación
    // estuviera desactivada, por ejemplo con "reducir movimiento" del sistema).
    toast.classList.add("toast-saliendo");
    const sacar = function () {
        toast.remove();
    };
    toast.addEventListener("animationend", sacar, {once: true});
    setTimeout(sacar, 250);
}

export function mostrarToast(mensaje, tipo) {
    const toast = document.createElement("div");
    toast.classList.add("toast", "toast-" + tipo);

    const texto = document.createElement("p");
    texto.textContent = mensaje;

    const cerrar = document.createElement("button");
    cerrar.type = "button";
    cerrar.classList.add("toast-cerrar");
    cerrar.setAttribute("aria-label", "Cerrar aviso");
    cerrar.textContent = "×";
    cerrar.addEventListener("click", function () {
        cerrarToast(toast);
    });

    toast.append(texto, cerrar);
    contenedorToasts.append(toast);

    const duracion = tipo === "error" ? 5000 : 3000;
    setTimeout(function () {
        cerrarToast(toast);
    }, duracion);
}

export function guardarAvisoPendiente(mensaje, tipo) {
    sessionStorage.setItem("aviso-pendiente", JSON.stringify({mensaje, tipo}));
}

export function mostrarAvisoPendiente() {
    const guardado = sessionStorage.getItem("aviso-pendiente");
    if (guardado === null) {
        return;
    }
    sessionStorage.removeItem("aviso-pendiente");
    const aviso = JSON.parse(guardado);
    mostrarToast(aviso.mensaje, aviso.tipo);
}