# Authly · Panel de administración (frontend)

Panel web para que el administrador de una organización gestione sus aplicaciones, los roles y permisos de cada una y sus usuarios. Está hecho con HTML, CSS y JavaScript sin librerías (módulos de JavaScript) y lo sirve Nginx.

## Estado

**Los seis casos de uso del panel están conectados a la API real.** Registro, login, aplicaciones (crear, listar, ver, editar, eliminar, regenerar secret), roles, usuarios y recuperación de contraseña hablan con el backend; ya no dependen de datos inventados para funcionar.

| Caso de uso | Pantalla |
|---|---|
| Registro de administrador | `register.html` |
| Inicio de sesión | `login.html` |
| Recuperación de contraseña | `recovery.html` |
| Aplicaciones (crear, ver, editar, eliminar, regenerar secret) | `apps.html` y `app.html` |
| Roles y permisos | `app.html`, pestaña «Roles» |
| Usuarios de una aplicación | `app.html`, pestaña «Usuarios» |

El panel también incluye transiciones y animaciones (entre páginas, en los modales, en las pestañas, al cambiar de tema, en los toasts y en los botones mientras procesan algo). Viven sobre todo en `css/transiciones.css` y `js/modules/components.js`, y se desactivan solas si la persona tiene «reducir movimiento» configurado en su sistema.

## Conexión con el backend

`js/modules/api.js` llama a la API real por defecto. Para seis áreas puntuales (listar y ver aplicaciones, eliminar aplicación, roles, usuarios, y recuperar contraseña) todavía queda, a propósito, un interruptor que permite volver a una simulación local si hiciera falta probar algo sin el backend levantado:

```js
const LISTAR_APLICACIONES_REAL = true;
const OBTENER_APLICACION_REAL = true;
const ELIMINAR_APLICACION_REAL = true;
const ROLES_REAL = true;
const USUARIOS_REAL = true;
const RECUPERACION_REAL = true;
```

Todos en `true` es el estado normal para trabajar y para subir cambios. El registro, el login, y crear/editar/regenerar una aplicación ya no tienen ningún camino de simulación: hablan con la API siempre.

## Estructura

```
frontend/
├── index.html, login.html, register.html, recovery.html   páginas de acceso
├── apps.html, app.html                                    panel
├── css/
│   ├── variables.css, base.css, components.css   estilos compartidos y animaciones
│   ├── auth.css, panel.css                        estilos propios de cada grupo de páginas
│   └── transiciones.css                           transición entre páginas y modo oscuro/claro
├── js/
│   ├── index.js, login.js, register.js, recovery.js, apps.js, app.js   un punto de entrada por página
│   ├── app/        módulos de app.html: datos (aplicacion.js, estado.js), roles (roles.js,
│   │                formulario-rol.js, eliminar-rol.js), usuarios (usuarios.js, editar-usuario.js,
│   │                eliminar-usuario.js) y la aplicación en sí (credenciales.js, editar-app.js,
│   │                eliminar-app.js)
│   └── modules/    código compartido (api.js, auth.js, components.js, notifications.js, theme.js,
│                    encabezado.js, utils.js, validators.js)
├── assets/img/     logos
└── default.conf    configuración de Nginx (es de infraestructura: no se toca)
```

## Cómo verlo

**Con Live Preview de VS Code**, para un vistazo rápido de la interfaz: abrir `login.html` con el botón derecho, «Show Preview». Como ahí no hay ningún backend detrás, cualquier acción que llame a la API (iniciar sesión, crear algo) va a fallar con un error de conexión; sirve para mirar pantallas, no para probar el flujo completo.

**Con Nginx, sin backend** (PowerShell, desde la raíz del repositorio), para probar que Nginx sirve bien los archivos:

```
docker run --rm -p 8080:80 --add-host api:127.0.0.1 -v "${PWD}/frontend:/usr/share/nginx/html:ro" -v "${PWD}/frontend/default.conf:/etc/nginx/conf.d/default.conf:ro" nginx:latest
```

El panel queda en `http://localhost:8080`. Mismo caso: las llamadas a `/api/` van a fallar, porque no hay backend.

**Con todo el proyecto, para probar de verdad**: `docker compose up -d --build` desde la raíz. Necesita el `.env` y un par de claves propias; los pasos están en `GUIA_CAMBIOS.md`, en la raíz del repositorio.

## Datos de ejemplo, para cuando se usa la simulación

Si alguno de los interruptores de arriba se pone en `false`, esa área vuelve a responder con datos inventados, guardados en el navegador. Todos están en `js/modules/api.js`.

| Para probar | Qué usar |
|---|---|
| Iniciar sesión | `admin@example.com` y `Ejemplo123-` |
| Código de verificación correcto | `123456` |
| Código vencido | `000000` |
| «Ese email ya está registrado» | `registrado@example.com` |
| «No se pudo enviar el correo» | `error-envio@example.com` |
| «El correo ya no está disponible» | `no-disponible@example.com` |
| CUIT ya registrado / ya no disponible | `11111111111` / `22222222222` |

Para volver a los datos iniciales, borrar en la consola del navegador `simulacion-aplicaciones`, `simulacion-roles` y `simulacion-usuarios` de `localStorage` y recargar. Para simular una sesión vencida: `localStorage.setItem("simulacion-token-vencido", "1")`.

## Reglas del equipo

- Las rutas del panel son relativas. Las llamadas a la API van a `/api/...`: Nginx quita el prefijo `/api` antes de reenviarlas al backend.
- No tocar `backend/` ni `frontend/default.conf`.
- No subir datos reales (correos, contraseñas, claves): el repositorio es público.
- Antes de subir un cambio, los interruptores de `api.js` tienen que quedar en `true`: se usan para probar puntualmente sin backend, no para dejarlos apagados.
- Antes de empezar a trabajar: `git pull`. Para subir: `git add frontend`, `git commit -m "..."` y `git push origin development`.

## Documentación

El contrato Panel–API y la guía de decisiones del frontend están en el Drive del equipo. El estado del backend, sus variables de entorno y cómo levantar el entorno completo están en `GUIA_CAMBIOS.md`, en la raíz del repositorio.