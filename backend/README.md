# Authly · Backend (API)

API REST de autenticación y gestión construida con FastAPI. Expone dos grupos de endpoints: el **panel de administración** (prefijo `/platform`) y la **API externa** para aplicaciones de terceros (prefijo `/auth`).

## Stack

- Python 3.13
- FastAPI + Uvicorn
- PostgreSQL (Supabase en producción, Alpine en local)
- JWT RS256 (PyJWT + cryptography)
- Argon2 para hashing de contraseñas
- Mailpit como servidor SMTP en desarrollo

## Estructura

```
backend/
├── main.py                    Punto de entrada, registro de routers y endpoints raíz
├── Dockerfile
├── requirements.txt
├── keys/                      Claves RSA para firma/verificación de JWT
├── app/
│   ├── config.py              Variables de entorno y configuración
│   ├── database.py            Conexión a PostgreSQL
│   ├── dependencies.py        Dependencias de FastAPI (ej: usuario_actual)
│   ├── errors.py              Manejo centralizado de errores HTTP
│   ├── middleware/
│   │   └── app_credentials.py Validación de credenciales de aplicación
│   ├── routers/
│   │   ├── applications.py    CRUD de aplicaciones (/platform/applications)
│   │   ├── roles.py           CRUD de roles (/platform/applications/{id}/roles)
│   │   ├── usuarios.py        Gestión de usuarios (/platform/applications/{id}/users)
│   │   ├── recuperacion.py    Recuperación de contraseña del admin (/recovery)
│   │   └── auth_api.py        API externa para apps de terceros (/auth)
│   ├── services/
│   │   ├── auth.py            Generación y verificación de JWT
│   │   ├── registro.py        Flujo de registro con código de verificación
│   │   ├── recuperacion.py    Flujo de recuperación de contraseña
│   │   ├── applications.py    Lógica de negocio de aplicaciones
│   │   ├── roles.py           Lógica de negocio de roles
│   │   ├── gestion_usuarios.py Lógica de negocio de usuarios
│   │   ├── users.py           Autenticación de usuarios
│   │   └── verification.py    Envío y validación de códigos
│   └── utils/
│       └── validators.py      Validaciones compartidas
└── tests/
    ├── conftest.py            Fixtures compartidos
    ├── test_applications.py
    ├── test_auth_endpoints.py
    ├── test_auth_tokens.py
    ├── test_errores_y_api_externa.py
    ├── test_recuperacion.py
    ├── test_roles.py
    ├── test_usuarios_panel.py
    ├── test_validators.py
    └── test_verification.py
```

## Endpoints

### Panel de administración (requieren JWT de admin)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/register/codigo` | Solicitar código de verificación para registro |
| `POST` | `/register/confirmar` | Confirmar registro con código |
| `POST` | `/login` | Iniciar sesión (devuelve JWT) |
| `GET` | `/me` | Datos del usuario autenticado |
| `POST` | `/platform/applications` | Crear aplicación |
| `GET` | `/platform/applications` | Listar aplicaciones |
| `GET` | `/platform/applications/{id}` | Detalle de una aplicación |
| `PUT` | `/platform/applications/{id}` | Editar aplicación |
| `DELETE` | `/platform/applications/{id}` | Eliminar aplicación |
| `POST` | `/platform/applications/{id}/regenerar-secret` | Regenerar client secret |
| `GET` | `/platform/applications/{id}/roles` | Listar roles de una aplicación |
| `POST` | `/platform/applications/{id}/roles` | Crear rol |
| `PUT` | `/platform/applications/{id}/roles/{rol_id}` | Editar rol |
| `DELETE` | `/platform/applications/{id}/roles/{rol_id}` | Eliminar rol |
| `GET` | `/platform/applications/{id}/users` | Listar usuarios de una aplicación |
| `PUT` | `/platform/applications/{id}/users/{user_id}` | Editar usuario |
| `DELETE` | `/platform/applications/{id}/users/{user_id}` | Eliminar usuario |

### Recuperación de contraseña (admin)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/recovery/codigo` | Solicitar código de recuperación |
| `POST` | `/recovery/confirmar` | Confirmar nueva contraseña |

### API externa (para aplicaciones de terceros)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/auth/public-key` | Obtener clave pública para verificar JWT |
| `POST` | `/auth/login` | Login de usuario final |
| `POST` | `/auth/register` | Registro de usuario final |
| `POST` | `/auth/register/verify` | Verificar email con código |
| `POST` | `/auth/password/recover` | Solicitar recuperación de contraseña |
| `POST` | `/auth/password/reset` | Resetear contraseña |
| `POST` | `/auth/permissions/verify` | Verificar permisos de un usuario |

## Tests

Desde la raíz del proyecto, con los contenedores levantados:

```bash
docker compose exec api pytest
```

Para correr un archivo específico:

```bash
docker compose exec api pytest tests/test_auth_endpoints.py -v
```

## Variables de entorno

Ver `.env.example` en la raíz del repositorio. Las principales para el backend:

| Variable | Descripción |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Conexión a PostgreSQL |
| `DB_SSLMODE` | Modo SSL (default: `require`) |
| `JWT_PRIVATE_KEY_PATH` / `JWT_PUBLIC_KEY_PATH` | Rutas a las claves RSA |
| `CODIGO_HMAC_KEY` | Clave para hashear códigos de verificación |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM` | Configuración de email |
