export function mostrarError(elemento, mensaje) {
    elemento.textContent = mensaje;
    elemento.classList.remove("oculto");
}

const contenedorToasts = document.createElement("div");
contenedorToasts.classList.add("contenedor-toasts");
contenedorToasts.setAttribute("role", "status");
contenedorToasts.setAttribute("aria-live", "polite");
document.body.append(contenedorToasts);

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
        toast.remove();
    });

    toast.append(texto, cerrar);
    contenedorToasts.append(toast);

    const duracion = tipo === "error" ? 5000 : 3000;
    setTimeout(function () {
        toast.remove();
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