# Authly · Panel de administración (frontend)

Panel web para que el administrador de una organización gestione sus aplicaciones, los roles y permisos de cada una y sus usuarios. Está hecho con HTML, CSS y JavaScript sin librerías (módulos de JavaScript) y lo sirve Nginx.

## Estado

| Caso de uso | Pantalla |
|---|---|
| Registro de administrador | `register.html` |
| Inicio de sesión | `login.html` |
| Recuperación de contraseña | `recovery.html` |
| Aplicaciones (crear, ver, editar, eliminar, regenerar secret) | `apps.html` y `app.html` |
| Roles y permisos | `app.html`, pestaña «Roles» |
| Usuarios de una aplicación | `app.html`, pestaña «Usuarios» |

**Todavía no está conectado al backend.** Las respuestas las simula `js/modules/api.js`, con datos guardados en el navegador. Cuando el backend esté listo, ese es el único archivo que se reemplaza: el resto del panel no cambia.

## Estructura

```
frontend/
├── index.html, login.html, register.html, recovery.html   páginas de acceso
├── apps.html, app.html                                    panel
├── css/        variables, base, components, auth, panel
├── js/
│   ├── index.js, login.js, register.js, recovery.js, apps.js, app.js   un punto de entrada por página
│   ├── app/        módulos de app.html (roles, usuarios, credenciales, modales)
│   └── modules/    código compartido (api, auth, validators, notifications...)
├── assets/img/     logos
└── default.conf    configuración de Nginx (es de infraestructura: no se toca)
```

## Cómo verlo

**Con Live Preview de VS Code** (la forma más simple, sin backend): abrir `login.html` con el botón derecho, «Show Preview».

**Con Nginx, sin backend** (PowerShell, desde la raíz del repositorio):

```
docker run --rm -p 8080:80 --add-host api:127.0.0.1 -v "${PWD}/frontend:/usr/share/nginx/html:ro" -v "${PWD}/frontend/default.conf:/etc/nginx/conf.d/default.conf:ro" nginx:latest
```

El panel queda en `http://localhost:8080`. Las llamadas a `/api/` van a fallar porque no hay backend, pero el panel todavía no las usa.

**Con todo el proyecto**: `docker compose up -d --build` desde la raíz. Necesita el `.env` y la clave privada, que se piden al equipo (ver `GUIA_CAMBIOS.md`).

## Datos de ejemplo

Todos los datos de prueba son inventados y están en `js/modules/api.js`.

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
- Antes de empezar a trabajar: `git pull`. Para subir: `git add frontend`, `git commit -m "..."` y `git push origin development`.

## Documentación

El contrato Panel–API y la guía de decisiones del frontend están en el Drive del equipo.