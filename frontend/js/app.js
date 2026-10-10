import { iniciarTema } from "./modules/theme.js";
import { exigirSesion } from "./modules/auth.js";
import { activarPestanas } from "./modules/components.js";
import { iniciarAplicacion, cargarAplicacion } from "./app/aplicacion.js";
import { iniciarCredenciales } from "./app/credenciales.js";
import { iniciarEditarApp } from "./app/editar-app.js";
import { iniciarEliminarApp } from "./app/eliminar-app.js";
import { iniciarRoles } from "./app/roles.js";
import { iniciarFormularioRol, abrirFormularioRol } from "./app/formulario-rol.js";
import { iniciarEliminarRol, abrirEliminarRol } from "./app/eliminar-rol.js";
import { iniciarEncabezado } from "./modules/encabezado.js";
import { iniciarUsuarios, cargarUsuariosSiHaceFalta } from "./app/usuarios.js";
import { iniciarEditarUsuario, abrirEditarUsuario } from "./app/editar-usuario.js";
import { iniciarEliminarUsuario, abrirEliminarUsuario } from "./app/eliminar-usuario.js";


exigirSesion();
iniciarTema();
iniciarEncabezado();

const pestanas = {
    roles: document.getElementById("pestana-roles"),
    usuarios: document.getElementById("pestana-usuarios")
};

const paneles = {
    roles: document.getElementById("panel-roles"),
    usuarios: document.getElementById("panel-usuarios")
};

iniciarAplicacion();
iniciarCredenciales();
iniciarEditarApp();
iniciarEliminarApp();
iniciarEliminarRol();
iniciarFormularioRol();
iniciarRoles({alEditar: abrirFormularioRol, alEliminar: abrirEliminarRol});
iniciarEditarUsuario();
iniciarEliminarUsuario();
iniciarUsuarios({
    alEditar: abrirEditarUsuario,
    alEliminar: abrirEliminarUsuario
});

activarPestanas(pestanas, paneles, function (nombre) {
    if (nombre === "usuarios") {
        cargarUsuariosSiHaceFalta();
    }
});
cargarAplicacion();