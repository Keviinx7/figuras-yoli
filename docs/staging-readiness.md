# Verificación de staging local

Fecha: 2026-09-13 · Commit base: `75ab8a8` (origin/main) · Entorno: local, `APP_ENV=staging`, sin publicación externa.

## A. Alcance

Staging verificado íntegramente contra una **copia aislada** de la base de datos
(`sqlite3` backup en `/tmp`) servida por Gunicorn en `127.0.0.1:8000`. No se
publicó nada en Internet, no se tocó `tienda.db`, ni se envió ni aceptó ningún
pago real ni WhatsApp real. Ninguna clave ni contraseña real aparece en este
documento.

## B. Entorno de staging

| Variable | Valor usado | Nota |
| --- | --- | --- |
| `APP_ENV` | `staging` | activa validación estricta de `SECRET_KEY` |
| `SECRET_KEY` | secreto temporal generado por `secrets.token_hex(32)` | nunca se escribe en git/documentos |
| `DATABASE_URL` | `sqlite:////tmp/yoli-staging/staging.db` | backup read-only de `instance/tienda.db` |
| `SESSION_COOKIE_SECURE` | `0` | HTTP local; producción conserva `1` |
| `TRUSTED_HOSTS` | `127.0.0.1,localhost` | alimenta `ALLOWED_HOSTS` de la app |
| `BEHIND_PROXY` | `0` | sin ProxyFix en staging |
| `HSTS_ENABLED` | `1` | se comprobó que **no** envía HSTS en HTTP |
| `BACKUP_DIR` | `/tmp/yoli-staging/backups` | destino de `backup-db` |
| `MAX_CONTENT_LENGTH_BYTES` | `65536` | para comprobar el 413 |

Gunicorn: `--bind 127.0.0.1:8000 --workers 2 --threads 1` (23.0.0, sync).

## C. Salud y encabezados

- `GET /health` → 200 `{"database":"ok","status":"ok"}`, `Cache-Control: no-store`, sin datos internos.
- Cabeceras de seguridad presentes en todas las respuestas:
  `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
  `X-Frame-Options: DENY`, `Permissions-Policy`, `Content-Security-Policy`
  (`default-src 'self'`), `Cache-Control` en blueprint administrativo.
- `Strict-Transport-Security` **ausente en HTTP** pese a `HSTS_ENABLED=1` (solo HTTPS), correcto.
- Cookie de sesión: `HttpOnly`, `SameSite=Lax`, sin `Secure` en HTTP local
  (por `SESSION_COOKIE_SECURE=0`; en producción el valor por defecto es `1`).

## D. Control de hosts

`config.py` deja `TRUSTED_HOSTS=None` (evita la integración de Flask 3.1 que
rompe el renderizado de errores) y la validación usa la lista real en
`ALLOWED_HOSTS` comparando el header `Host` crudo.

- `Host: 127.0.0.1:8000` → 200
- `Host: localhost:8000` → 200
- `Host: evil.example.com` → 400 con "Host no autorizado.", sin traceback.

## E. Autenticación y sesión

Con usuarios temporales creados solo en la copia de staging:

- `POST /login` correcto → 302 a `/admin/`; la app **rota el token CSRF** tras
  autenticar (`session.clear()` + token nuevo): los forms siguientes usan el
  token fresco, nunca el de la página de login.
- `GET /admin/` autenticado → 200 (Resumen); `GET /login` ya autenticado → 302.
- `POST /logout` → 302 a `/login` y cookie `session` vencida
  (`Expires=1970`, `Max-Age=0`); `GET /admin/` tras logout → 302 (sesión realmente inválida).
- Login con credenciales erróneas → 401, re-render sin datos sensibles.

## F. Flujo comercial completo

`tests/browser_commercial.mjs` contra Gunicorn staging: cliente → material →
cálculo → receta → cotización → factura interna → pago de prueba.
**69 checks pasaron** sobre la copia, con vista de inventario de materiales.

## G. Concurrencia (Gunicorn + SQLite, 2 worker)

Script propio contra la copia:

- 12 logins correctos en paralelo → 12×200, sin `OperationalError`.
- 10 cotizaciones concurrentes (login + POST por hilo, token fresco) →
  10×302 a `/admin/cotizaciones/<id>`, **10 números únicos**, contar antes/después
  exacto, `count(distinct quote_number)==count(*)`.
- Sin "database is locked" en el error log. Los write paths (login, cotizaciones)
  serializan con `BEGIN IMMEDIATE`; GoUp/Progreso acumulado en el mismo file
  SQLite en una sola máquina.

**Límite honesto:** SQLite admite concurrencia limitada a un escritor y queda
acotado al host de la app. Para escalado horizontal o multi-instancia se migra a
PostgreSQL (portabilidad ya cubierta y probada en `tests/test_production.py`).

## H. Manejo de errores

| Caso | Resultado |
| --- | --- |
| `GET /no-existe` | 404 página amigable, sin traceback |
| vendedor en `GET /admin/usuarios` (solo admin) | 403, sin traceback |
| POST con cuerpo > 64 KB (`MAX_CONTENT_LENGTH`) | 413 "SOLICITUD DEMASIADO GRANDE" |
| 10 contraseñas incorrectas seguidas | 10×401 y la siguiente → 429 "Espere 15 minutos" |
| App desechable con `/boom` que lanza `RuntimeError` | 500 página amigable; traceback solo en el error log del server |

## I. Estáticos

- `/`, `/catalogo`, `/carrito`, `/favoritos`, `/producto/fy-an-001` → 200.
- CSS/JS: `/static/css/styles.css`, `/static/js/{app,admin,cart,catalog,favorites}.js` → 200.
- Imágenes: `/static/img/products/FY.AN.001.png` → 200 (los `file_path` se sirven
  bajo `/static`, donde el archivo existe en disco).

## J. `DATABASE_URL` desde entorno

`/health` responde `"database":"ok"` usando `DATABASE_URL` del entorno apuntando
a la copia; la app muestra 173 productos y 17 categorías de esa copia, no de
`tienda.db`.

## K. Backup y restauración

`flask --app wsgi backup-db` con entorno staging:

- Genera `backups/tienda-backup-<timestamp>.db` (`0600`).
- `PRAGMA integrity_check` del backup → `('ok',)`.
- Restaurado a `/tmp/yoli-staging/restored.db` vía `sqlite3 backup`: mismas
  tablas y conteos idénticos (products 173, categories 17, quotes, invoices,
  customers 5, number_sequences 2).

## L. Suites completas (estado esperado)

| Suite | Resultado |
| --- | --- |
| `python -m unittest discover -s tests` | 136 OK |
| `node tests/test_storage.cjs` | 11 OK |
| `node tests/test_admin_js.cjs` | 6 OK |
| `node --check app/static/js/*.js` | sin errores de sintaxis |
| `browser_check.mjs` (público) contra staging | 89 checks OK |
| `browser_commercial.mjs` contra staging | 69 checks OK |
| Datos de la copia | 173 productos · 17 categorías |

Sin bugs detectados durante la verificación; por diseño no hubo cambios de código,
por lo que no se generó commit nuevo.

## M. Notas de despliegue

- En HTTP local la cookie debe ser `Secure=0`; en el despliegue real (HTTPS tras
  proxy) usar `BEHIND_PROXY=1`, `SESSION_COOKIE_SECURE=1` y los hosts públicos en
  `TRUSTED_HOSTS` (guía completa en `docs/production-deploy.md`).
- El 429 de login es compartido por IP (hash de `REMOTE_ADDR`); para rate-limiting
  por proxy real se activa `PERMANENT_SESSION_LIFETIME`/PROXY si corresponde.
- La migración a PostgreSQL (si algún día se requiere escala horizontal) ya está
  soportada: secuencias, vulnerabilidad de contabilidad y búsqueda son
  dialect-aware; ver `tests/test_production.py`.