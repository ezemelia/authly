<p align="center">
  <img src="frontend/assets/img/logo_horizontal.png" alt="Authly" width="350">
</p>

<p align="center">
  API de autenticación y gestión de usuarios con panel de administración web.
</p>

---

## Descripción

Authly es una plataforma de autenticación como servicio (AaaS) que permite a aplicaciones de terceros registrar usuarios, autenticarlos mediante JWT y gestionar roles y permisos. Incluye un panel de administración web para la gestión visual de aplicaciones, usuarios y roles.

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Backend / API | Python 3.13 · FastAPI · Uvicorn |
| Base de datos | PostgreSQL 17 (Supabase en producción, Alpine en local) |
| Autenticación | JWT (RS256) · Argon2 |
| Frontend | HTML · CSS · JavaScript vanilla |
| Servidor web | Nginx |
| Email (desarrollo) | Mailpit |
| Contenedores | Docker · Docker Compose |

## Requisitos previos

- [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/install/)
- Git

## Instalación y ejecución

1. Clonar el repositorio y posicionarse en la rama de desarrollo:

```bash
git clone https://github.com/ezemelia/authly.git
cd authly
git checkout development
```

2. Crear el archivo de variables de entorno a partir del ejemplo:

```bash
cp .env.example .env
```

3. Completar las variables en `.env` con los datos correspondientes (base de datos, claves JWT, HMAC key).

4. Levantar los servicios:

```bash
docker compose up --build
```

5. Acceder a:

| Servicio | URL |
|---|---|
| Frontend | http://localhost:8080 |
| API docs (Swagger) | http://localhost:8000/docs |
| Mailpit (emails de desarrollo) | http://localhost:8025 |

## Estructura del proyecto

```
authly/
├── backend/
│   ├── app/
│   │   ├── middleware/       # Credenciales de aplicación (X-Client-Id / X-Client-Secret)
│   │   ├── routers/          # Endpoints: aplicaciones, roles, usuarios, recuperación, auth externa
│   │   ├── services/         # Lógica de negocio de cada área
│   │   ├── utils/            # Validadores y utilidades
│   │   └── errors.py         # Formato de error único para todas las rutas del panel
│   ├── keys/                 # Claves públicas/privadas JWT
│   ├── tests/                # Tests unitarios (pytest)
│   ├── Dockerfile
│   ├── main.py
│   ├── README.md
│   └── requirements.txt
├── frontend/
│   ├── assets/               # Imágenes y recursos
│   ├── css/                  # Estilos, incluidas las transiciones y animaciones
│   ├── js/
│   │   ├── app/              # Módulos del panel: aplicaciones, roles, usuarios
│   │   └── modules/          # Módulos compartidos (api, auth, components, notifications...)
│   ├── *.html                # Páginas
│   └── README.md
├── docs/                     # Documentación, diagramas y manual de usuario
├── compose.yml
├── .env.example
└── GUIA_CAMBIOS.md
```

## Tests

```bash
docker compose exec api pytest
```

## Integrantes

| Nombre |
|---|
| Felipe Monetti |
| Valentino Castellano |
| Valentino Bustamante |
| Ezequiel Melía |
| Lucía Marconi |
| Felipe Cazón |

