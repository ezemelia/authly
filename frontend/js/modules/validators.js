export function validarCampo(campo, error) {
    if (campo.value.trim() === "") {
        error.classList.remove("oculto");
        return false;
    }
    error.classList.add("oculto");
    return true;
}

export function validarEmail(campo, error) {
    const patronEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (campo.value.trim() === "") {
        error.textContent = "Campo incompleto. Ingrese su correo.";
        error.classList.remove("oculto");
        return false;
    }

    if (!patronEmail.test(campo.value.trim())) {
        error.textContent = "Ingrese un correo válido.";
        error.classList.remove("oculto");
        return false;
    }
    error.classList.add("oculto");
    return true;
}

export function validarPass(campo, error) {

    if (campo.value === "") {
        error.textContent = "Campo incompleto. Ingrese su contraseña.";
        error.classList.remove("oculto");
        return false;
    }

    let aviso = "";

    if (campo.value.length < 10) {
        aviso += "La contraseña debe ser de mínimo 10 caracteres. ";
    }

    if (!/[A-Z]/.test(campo.value)) {
        aviso += "Falta una mayúscula. ";
}

    if (!/[a-z]/.test(campo.value)) {
        aviso += "Falta una minúscula. ";
    }

    if (!/[0-9]/.test(campo.value)) {
        aviso += "Falta un número. ";
    }

    if (!/[^A-Za-z0-9]/.test(campo.value)) {
        aviso += "Falta un caracter especial. ";
    }

    if (aviso !== "") {
        error.textContent = aviso;
        error.classList.remove("oculto");
        return false;
    }

    error.classList.add("oculto");
    return true;
}

export function validarConfirmacion(campo, campoPass, error) {
    if (campo.value !== campoPass.value) {
        error.textContent = "Las contraseñas no coinciden.";
        error.classList.remove("oculto");
        return false;
    }
    
    error.classList.add("oculto");
    return true;
}

export function validarCuit(campo, error) {
    const patronCuit = /^[0-9]{11}$/;
    if (campo.value.trim() === "") {
        error.textContent = "Campo incompleto. Ingrese el CUIT.";
        error.classList.remove("oculto");
        return false;
    }

    if (!patronCuit.test(campo.value.trim())) {
        error.textContent = "Ingrese un CUIT válido (11 números sin espacios ni guiones).";
        error.classList.remove("oculto");
        return false;
    }
    error.classList.add("oculto");
    return true;
}

export function validarCodigo(campo, error) {
    const patronCodigo = /^[0-9]{6}$/;
    if (campo.value.trim() === "") {
        error.textContent = "Campo incompleto. Ingrese el código de 6 dígitos.";
        error.classList.remove("oculto");
        return false;
    }

    if (!patronCodigo.test(campo.value.trim())) {
        error.textContent = "Ingrese un código válido (6 números).";
        error.classList.remove("oculto");
        return false;
    }
    error.classList.add("oculto");
    return true;
}