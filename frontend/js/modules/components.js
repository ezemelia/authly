export function irAlPaso(pasos, indicadores, desde, hasta) {
    pasos[desde].classList.add("oculto");
    pasos[hasta].classList.remove("oculto");
    indicadores[desde].classList.remove("activo");
    indicadores[desde].removeAttribute("aria-current");
    indicadores[hasta].classList.add("activo");
    indicadores[hasta].setAttribute("aria-current", "step");
}

export function activarCopia(boton, obtenerTexto) {
    const textoOriginal = boton.textContent;
    boton.addEventListener("click", async function() {
        await navigator.clipboard.writeText(obtenerTexto());
        boton.textContent = "Copiado";
        setTimeout(function () {
            boton.textContent = textoOriginal;
        }, 2000);
    });
}

export function activarOjo(boton, campo) {
    boton.addEventListener("click", function () {
        if (campo.type === "password") {
            campo.type = "text";
            boton.setAttribute("aria-pressed", "true");
        } else {
            campo.type = "password";
            boton.setAttribute("aria-pressed", "false");
        }
    });
}

export function activarPestanas(pestanas, paneles, alActivar) {
    for (const nombre in pestanas) {
        pestanas[nombre].addEventListener("click", function () {
            for (const otro in pestanas) {
                const activa = otro === nombre;
                pestanas[otro].setAttribute("aria-selected", activa ? "true" : "false");
                paneles[otro].classList.toggle("oculto", !activa);
            }
            if (alActivar !== undefined) {
                alActivar(nombre);
            }
        });
    }
}

function paginasVisibles(actual, totalPaginas) {
    const visibles = [];
    for (let numero = 1; numero <= totalPaginas; numero++) {
        const esExtremo = numero === 1 || numero === totalPaginas;
        const esCercana = Math.abs(numero - actual) <= 1;
        if (esExtremo || esCercana) {
            visibles.push(numero);
        } else if (visibles[visibles.length - 1] !== "…") {
            visibles.push("…");
        }
    }
    return visibles;
}

function crearBotonPagina(texto, etiqueta, alHacerClic) {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.textContent = texto;
    boton.setAttribute("aria-label", etiqueta);
    boton.addEventListener("click", alHacerClic);
    return boton;
}

export function crearPaginador(nav, alCambiar) {
    function mostrar(paginaActual, total, tamanio) {
        nav.replaceChildren();
        const totalPaginas = Math.ceil(total / tamanio);

        if (totalPaginas <= 1) {
            nav.classList.add("oculto");
            return;
        }
        nav.classList.remove("oculto");

        const anterior = crearBotonPagina("Anterior", "Página anterior", function () {
            alCambiar(paginaActual - 1);
        });
        anterior.disabled = paginaActual === 1;
        nav.append(anterior);

        for (const elemento of paginasVisibles(paginaActual, totalPaginas)) {
            if (elemento === "…") {
                const puntos = document.createElement("span");
                puntos.textContent = "…";
                puntos.setAttribute("aria-hidden", "true");
                nav.append(puntos);
            } else {
                const boton = crearBotonPagina(elemento, "Ir a la página " + elemento, function () {
                    alCambiar(elemento);
                });
                if (elemento === paginaActual) {
                    boton.setAttribute("aria-current", "page");
                }
                nav.append(boton);
            }
        }

        const siguiente = crearBotonPagina("Siguiente", "Página siguiente", function () {
            alCambiar(paginaActual + 1);
        });
        siguiente.disabled = paginaActual === totalPaginas;
        nav.append(siguiente);
    }

    return {mostrar};
}

