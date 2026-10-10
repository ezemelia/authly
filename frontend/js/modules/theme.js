export function iniciarTema() {
    const temaGuardado = localStorage.getItem("tema");
    const botonTema = document.getElementById("cambiar-tema");
    if (temaGuardado === "oscuro") {
        document.documentElement.setAttribute("data-tema", "oscuro");
        botonTema.setAttribute("aria-label", "Cambiar a modo claro");
    }
    botonTema.addEventListener("click", function () {
        if (document.documentElement.getAttribute("data-tema") === "oscuro") {
            document.documentElement.removeAttribute("data-tema");
            localStorage.setItem("tema", "claro");
            botonTema.setAttribute("aria-label", "Cambiar a modo oscuro" );
        } else {
            document.documentElement.setAttribute("data-tema", "oscuro");
            localStorage.setItem("tema", "oscuro");
            botonTema.setAttribute("aria-label", "Cambiar a modo claro" );
        }
    });
}
