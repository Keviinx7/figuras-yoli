# Correo a clientes: verificación, recuperación y notificaciones

El portal de clientes usa un transporte de correo opcional y aislado. En
desarrollo la tienda funciona sin ningún correo; solo cuando se configura un
remitente real (SMTP) se activan las funciones que dependen de él. Nunca se
simula un envío que no ocurrió.

## Qué se puede enviar

- **Verificación de correo** (`verify_email`): tras `registro` o cambio de
  correo, si `EMAIL_VERIFICATION_ENABLED=1` y hay transporte disponible.
- **Recuperación de contraseña** (`reset_password`): enlace temporal de un solo
  uso para restablecer la clave, si `ACCOUNT_RECOVERY_ENABLED=1`.
- **Confirmación y cambios de estado de solicitudes**: al crear un pedido y al
  cambiar su estado real (`pending→processing→completed/rejected`), si
  `ORDER_EMAIL_NOTIFICATIONS_ENABLED=1`. Guardar el mismo estado NO reenvía nada.

Los tres flujos comparten el mismo transporte, pero sus propósitos están
separados: un enlace de verificación no sirve para recuperar la contraseña y
viceversa.

## Qué NUNCA se envía ni expone

Los correos son de solo lectura para el cliente: nunca incluyen costos,
recetas, materiales, mano de obra, markup, margen, ganancia ni notas internas.
El catálogo oficial no tiene precios fijos; los correos repiten
"Los precios se confirman según tamaño y personalización". No se imprimen ni
registran direcciones, cuerpos, tokens ni credenciales SMTP en logs.

## Arquitectura

`app/services/mail.py` es el transporte reutilizable:

- `configure_mail(app)`: valida la configuración al arrancar y rechaza
  configuraciones inválidas (transporte desconocido, TLS+SSL a la vez, SMTP sin
  `MAIL_FROM_ADDRESS`/host, `PUBLIC_BASE_URL` malformada, `fake` en
  staging/production, características activas sin `MAIL_ENABLED`, etc.).
- `send_mail(recipient, subject, body)`: construye el mensaje y entrega con
  SMTP (TLS o SSL) o con el backend `fake` (memoria, solo pruebas). Ante
  cualquier fallo registra un warning genérico y devuelve `failed`; nunca loguea
  el detalle de la excepción ni expone credenciales.
- `available()`: `True` solo si `MAIL_ENABLED` y el backend es `smtp`/`fake`.
- `public_link(path)`: construye enlaces con `PUBLIC_BASE_URL`, jamás el
  `Host` del navegador (evita *host-header poisoning*).
- `queue_order_email(req)` / `deliver_order_mail(row_id)`: cola durable de
  mensajes de pedido. La fila se crea EN la misma transacción comercial; la
  entrega ocurre en una transacción separada después del commit. Si el envío
  falla, el pedido ya creado NO se elimina ni se revierte; la fila queda
  pendiente y `flask retry-order-mail` la reintenta. No se requiere Celery/Redis.

`app/services/account_email.py` gestiona tokens y límites:

- `issue_token(account, purpose)`: token aleatorio de 32 bytes
  (`secrets.token_urlsafe(32)`). Solo se persiste el digest SHA-256 del token,
  nunca el token en claro. Revoca los tokens del mismo propósito antes de emitir
  el nuevo. Tiene expiración (`*_LIFETIME_HOURS`) y se liga al hash de la
  contraseña y al correo del momento.
- `find_token(token, purpose)`: valida digest, propósito, expiración, cuenta
  activa, correo y credencial actuales. No consume.
- `consume_token(token, purpose)`: consume atómicamente (`used_at` en UPDATE
  con condición) y devuelve la cuenta; un mismo token solo sirve una vez.
- `revoke_tokens(account[, purpose])`: marca `used_at` de los tokens vigentes;
  es lo que garantiza que desactivar, cambiar de correo o restablecer
  contraseña invaliden enlaces pendientes.
- `throttle(scope, identity, limit, seconds)`: contadores atómicos por IP e
  identidad (correo/cuenta) incluso para correos que no existen.

## Seguridad de tokens

1. **Criptográficamente seguro**: `secrets.token_urlsafe(32)`.
2. **No en claro**: solo el digest SHA-256 se persiste.
3. **Caducan**: `expires_at` se compara contra reloj UTC.
4. **Un solo uso**: consumo atómico con `used_at`.
5. **Propósitos separados**: columna `purpose` con restricción
   (`verify_email`/`reset_password`); un enlace de un propósito nunca
   valida el otro.
6. **Cambio de contraseña**: rota `session_token` (mata sesiones) y liga los
   tokens al hash previo (`credential_digest`), así los enlaces emitidos antes
   quedan sin efecto.
7. **Desactivar cuenta** revoca los tokens pendientes (`used_at`); **reactivar
   no revive** tokens antiguos.
8. **Cambio de correo** revoca verificaciones anteriores; además el token se
   liga al correo (`email`) vigente.
9. Los tokens no se imprimen en logs (filtro `RedactAccountLinks`), no se
   muestran al admin y no van en documentación ni capturas. Nginx y Gunicorn de
   ejemplo apagan el log de rutas para que las URLs portador no queden grabadas.

## Configuración

Ver `.env.example` para todos los valores. Resumen:

| Variable | Default | Uso |
|---|---|---|
| `MAIL_ENABLED` | `false` | Apaga todo el transporte si no está en `1`. |
| `MAIL_BACKEND` | `smtp` | `smtp` (real), `fake` (solo pruebas locales) o `disabled`. |
| `SMTP_HOST` / `SMTP_PORT` | vacío / `587` | Servidor y puerto SMTP. |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | vacío | Credenciales opcionales (ambas o ninguna). |
| `SMTP_USE_TLS` / `SMTP_USE_SSL` | `true` / `false` | Nunca ambas a la vez. |
| `MAIL_FROM_ADDRESS` / `MAIL_FROM_NAME` | vacío / nombre | Remitente. |
| `PUBLIC_BASE_URL` | `http://localhost:5000` | Base absoluta de los enlaces; no depende del navegador. |
| `EMAIL_VERIFICATION_ENABLED` | `false` | Activa la verificación de correo. |
| `EMAIL_VERIFICATION_LIFETIME_HOURS` | `24` | Vigencia de los enlaces de verificación. |
| `ACCOUNT_RECOVERY_ENABLED` | `false` | Activa la recuperación de contraseña. |
| `ACCOUNT_RECOVERY_LIFETIME_HOURS` | `1` | Vigencia de los enlaces de recuperación. |
| `ORDER_EMAIL_NOTIFICATIONS_ENABLED` | `false` | Activa confirmaciones y cambios de estado. |

Reglas importantes:

- En staging/production el arranque exige `MAIL_ENABLED=1` con backend `smtp`,
  TLS o SSL activo, `MAIL_FROM_ADDRESS` válido y `PUBLIC_BASE_URL` https.
  `MAIL_BACKEND=fake` está prohibido fuera de pruebas.
- Los enlaces de verificación/recuperación usan `PUBLIC_BASE_URL`; cambiar
  contraseña o desactivar la cuenta invalida cualquier enlace ya emitido.
- Sin SMTP configurado (o `MAIL_ENABLED=false`), el registro/portal funcionan
  igual; la recuperación muestra el mensaje honesto de escribir por WhatsApp y
  el panel informa que la verificación no está disponible. Nada finge un envío.

## Pruebas

- `tests/test_customer_email.py` cubre verificación (válida, inválida,
  expirada, reutilizada, reenvío, cuenta desactivada, reactivación que no
  revive), recuperación (mensaje genérico, expiración, reutilización, nuevo
  password funciona y el viejo falla, sesiones revocadas), notificaciones
  (confirmación, cambio real, mismo estado sin duplicado, fallo SMTP que no
  elimina el pedido), seguridad (CSRF, IDOR, rate-limit, separación
  cliente/staff, `PUBLIC_BASE_URL` contra host-header poisoning, sin secretos
  en logs) y consumo atómico con rollback.
- El backend `fake` acumula mensajes en memoria de la app de pruebas
  (`app.extensions['mail_outbox']`); solo el fixture aislado
  `tests/browser_commercial_server.py` expone una captura con clave secreta
  (`/__test/mail`) para el E2E `tests/browser_customer.mjs --email-e2e`.
- Nunca se usa SMTP real ni una base con datos no desechables en las pruebas.