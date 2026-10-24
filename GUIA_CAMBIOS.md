# Guía de cambios: backend conectado a Supabase

Resumen de lo que se hizo para que la API de Authly funcione contra la base de Supabase.

## 1. Levantar el proyecto

1. Copiar `.env.example` a `.env` y completar las variables `DB_*` con los datos de
   Supabase (**Project Settings → Database → Connection string → Session pooler**).
   Usar el pooler y no el host directo: el directo es solo IPv6 y Docker en Mac suele no llegar.
2. Poner `private_key.pem` en `backend/keys/` (no está en el repo, se pide al equipo).
3. Levantar:

   ```bash
   docker compose up -d --build
   ```

4. Frontend en <http://localhost:8080>. La API se alcanza por `/api/...` (nginx quita el `/api`).

El Postgres local ya no se usa por defecto. Si se lo necesita: `docker compose --profile local-db up -d`.

## 2. Qué estaba fallando

| Problema | Causa | Solución |
|---|---|---|
| La API se caía al arrancar | Faltaba `backend/keys/private_key.pem` (está en `.gitignore`) | Pedir la clave al equipo |
| 404 en aplicaciones | Nginx quita `/api/`, pero el router tenía `/api/platform/applications` | Prefijo cambiado a `/platform/applications` |
| La API apuntaba a un Postgres vacío | `compose.yml` fijaba la base local | Ahora toma `DB_*` del `.env` (Supabase, con SSL) |
| `relation "applications" does not exist` | El backend asumía tablas distintas a las reales | Se adaptó el código al esquema `authly` |
| Login imposible con las cuentas existentes | Los hashes de `administrador` son argon2, no bcrypt | Verificación con `argon2-cffi` |

## 3. Esquema de la base

El esquema lo define el compañero encargado de la base y vive en el schema **`authly`**
(la conexión hace `SET search_path TO authly`). No crear ni modificar tablas desde el backend.

Tablas que usa hoy la API: `organizacion`, `administrador`, `aplicacion`, `codigo_administrador`.
Los ids son uuid. `aplicacion` se identifica por `client_id`. Hay un solo administrador por organización.

## 4. Endpoints

Desde el navegador se llaman con el prefijo `/api`. El token va en `Authorization: Bearer <token>`.

| Endpoint | Entrada | Respuesta |
|---|---|---|
| `POST /register/codigo` | `nombre`, `apellido`, `email`, `password`, `organizacion`, `cuit` | 200, o 400 `{detail, campo, reinicio}` |
| `POST /register/confirmar` | lo mismo + `codigo` | 201 `{id, email, organizacion_id}`, o 400 igual que arriba |
| `POST /login` | `email`, `password` | `{access_token, token_type}`, o 401 |
| `GET /me` | token | `{id, nombre, apellido, email, organizacion_id}` |
| `GET /platform/applications/` | token | lista de aplicaciones de **su** organización |
| `POST /platform/applications/` | `nombre`, `descripcion` + token | `{nombre, client_id, client_secret}` (el secret se ve una sola vez) |
| `POST /platform/applications/{client_id}/regenerar-secret` | token | `{client_id, client_secret}` |

En los errores de registro, `campo` indica qué input marcar y `reinicio: true` significa volver al primer paso.

## 5. Cómo funciona

- **Registro:** dos pasos. Primero se pide un código de 6 dígitos (vence en 10 min, se guarda hasheado en
  `codigo_administrador`, máximo 5 intentos). Al confirmarlo se crean la organización y el administrador
  en una sola transacción. Código: `backend/app/services/registro.py`.
- **Login:** compara la contraseña con argon2 y devuelve un JWT (RS256) con el uuid del administrador.
  Mismo error si el email no existe o la contraseña es incorrecta.
- **Aplicaciones:** la organización sale del administrador logueado (`app/dependencies.py`).
  Un administrador solo ve y modifica las de su organización. El secret se guarda como SHA-256,
  igual que las aplicaciones que ya existían.

## 6. Pendiente

- **Envío real del email con el código.** Hoy se imprime en los logs de la API
  (`docker compose logs api`). Hay un `TODO` en `registro.py`.
- **Conectar el frontend.** `frontend/js/modules/api.js` simula todo con datos en memoria y no hace `fetch`.
  Lo hace otro compañero; la tabla de endpoints de arriba es el contrato.
- **Recuperación de contraseña:** el esquema la soporta (`proposito = 'recuperacion'`), falta el endpoint.
- **Contraseña de Supabase:** se compartió por chat durante el desarrollo, conviene resetearla.

## 7. Tests

52 tests, corren contra la base real de Supabase. Todo lo que crean se borra solo
(emails `@test-authly.com` y CUITs que empiezan con `9999999999`).

```bash
docker compose cp backend/tests api:/app/tests
docker compose exec api python -m pytest -q
```

- Tardan unos 8 minutos (cada test hace varias consultas remotas).
- **No correrlos dos veces a la vez**: comparten los mismos datos de prueba y se pisan.
