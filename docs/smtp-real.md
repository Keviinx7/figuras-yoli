# Brevo SMTP: diagnóstico y prueba local de verificación

## Diagnóstico del 2026-09-14

La auditoría de `create_app()` reprodujo dos configuraciones diferentes:

| Valor efectivo | Arranque normal sin archivo seleccionado | Archivo privado cargado explícitamente |
|---|---|---|
| MAIL_ENABLED | false | true |
| MAIL_BACKEND | smtp | smtp |
| SMTP_HOST | vacío | smtp-relay.sendinblue.com |
| SMTP_PORT | 587 | 587 |
| SMTP_USE_TLS / SMTP_USE_SSL | true / false | true / false |
| SMTP_USERNAME_PRESENT / SMTP_PASSWORD_PRESENT | false / false | true / true |
| MAIL_FROM_ADDRESS_PRESENT | false | true |
| EMAIL_VERIFICATION_ENABLED | false | true |
| ACCOUNT_RECOVERY_ENABLED | false | false |
| ORDER_EMAIL_NOTIFICATIONS_ENABLED | false | false |

El cargador anterior solo leía `.env`. Tener `.env.smtp-manual` en disco no lo
activaba. Con la feature apagada, el registro guardaba la cuenta y no generaba
el token ni invocaba SMTP. No hay discrepancia entre nombres de variables.
El archivo privado también apuntaba a la DB principal: se debe sobrescribir
`DATABASE_URL` para esta prueba. No se modificó esa DB.

El registro existente ya implementa cuenta → token → construcción del mensaje →
`send_mail`. La corrección conserva ese flujo y añade selección explícita del
archivo y diagnóstico seguro. Un fallo de transporte conserva la cuenta y revoca
el token del intento fallido; el usuario puede solicitar otro tras resolverlo.
No hay cola durable de verificaciones: se envían sincrónicamente. La tabla
`order_email_outbox` corresponde únicamente a notificaciones de solicitudes.

### Incidente TLS regional

En este entorno/región el desarrollador comprobó que `smtp-relay.brevo.com:587`
respondía con un certificado incompatible con el hostname; los nombres observados
incluían `smtp-relay-offshore-southamerica-east-v2.sendinblue.com` y
`smtp-relay.sendinblue.com`. Luego `smtp-relay.sendinblue.com:587` obtuvo
`Verify return code: 0 (ok)` y `SMTP_AUTH_OK` con STARTTLS.

Se conserva ese host explícito. No es un fallback automático ni una garantía para
otras regiones. Nunca desactivar certificate verification, `check_hostname` o usar
`ssl._create_unverified_context()`. El transporte y el diagnóstico usan
`ssl.create_default_context()`. Si otro hostname falla, detenerse y resolver el
certificado/host con el proveedor; no eludir TLS.

## Variables privadas

| Variable | Valor/uso |
|---|---|
| MAIL_ENABLED | true durante esta prueba |
| MAIL_BACKEND | smtp |
| SMTP_HOST | smtp-relay.sendinblue.com |
| SMTP_PORT | 587 |
| SMTP_USE_TLS | true (STARTTLS) |
| SMTP_USE_SSL | false |
| SMTP_USERNAME | SMTP login de Brevo |
| SMTP_PASSWORD | Clave SMTP dedicada, nunca contraseña normal ni API key |
| MAIL_FROM_ADDRESS | Remitente verificado de Brevo |
| MAIL_FROM_NAME | Nombre visible del remitente |
| PUBLIC_BASE_URL | http://127.0.0.1:5003 para prueba local |
| EMAIL_VERIFICATION_ENABLED | true |
| ACCOUNT_RECOVERY_ENABLED | false |
| ORDER_EMAIL_NOTIFICATIONS_ENABLED | false |

Vigencias opcionales: `EMAIL_VERIFICATION_LIFETIME_HOURS=24`,
`ACCOUNT_RECOVERY_LIFETIME_HOURS=1`; enteros entre 1 y 168. TLS implícito, si se
utiliza en otra configuración, requiere puerto 465, SSL=true y TLS=false.
Nunca ambos flags a la vez.

## Arranque limpio con archivo privado

`YOLI_ENV_FILE` es una variable **del proceso** que selecciona un archivo en lugar
de `.env`; puede tener cualquier nombre. Si no se indica, continúa la lectura
normal de `.env`. Si el archivo seleccionado no se puede leer, el arranque falla
con un mensaje genérico. Las variables ya exportadas prevalecen sobre el archivo.
Reiniciar la aplicación después de cambiar configuración. El cargador no ejecuta
shell ni expande variables; admite comillas exteriores y comentarios en líneas
propias, no comentarios al final de valores. No usar `source`, `set -x`, volcados
de entorno/configuración, depuración SMTP ni secretos en argumentos.

Si ya existe el archivo privado, no sobrescribirlo. Para una instalación nueva:

```bash
(umask 077; cp -n .env.example .env.smtp-manual)
chmod 600 .env.smtp-manual
git check-ignore .env .env.smtp-manual
```

Editar localmente sin capturas ni logs. Jamás usar `git add -f`. Antes de probar:

```bash
git status --short --branch
git branch --show-current
git fetch origin
git rev-list --left-right --count main...origin/main
```

Trabajar con `main` limpio y `0 0`. Usar una DB nueva; no copiar clientes ni colas
comerciales. Si fuera imprescindible modificar una DB existente, hacer antes un
respaldo verificado con `flask --app run backup-db` (SQLite). Aquí no se necesita.

En una terminal nueva, desde la raíz, exportar solo estas variables no secretas:

```bash
unset SMTP_HOST SMTP_PORT SMTP_USERNAME SMTP_PASSWORD SMTP_USE_TLS SMTP_USE_SSL
unset MAIL_FROM_ADDRESS MAIL_FROM_NAME
export YOLI_ENV_FILE="$PWD/.env.smtp-manual"
export APP_ENV=development
export DATABASE_URL="sqlite:///$PWD/instance/smtp-verification-audit.db"
export PUBLIC_BASE_URL=http://127.0.0.1:5003
export MAIL_ENABLED=true MAIL_BACKEND=smtp
export EMAIL_VERIFICATION_ENABLED=true
export ACCOUNT_RECOVERY_ENABLED=false ORDER_EMAIL_NOTIFICATIONS_ENABLED=false
export SESSION_COOKIE_SECURE=false BEHIND_PROXY=false HSTS_ENABLED=false
export TRUSTED_HOSTS=127.0.0.1 LOG_LEVEL=INFO LOG_FILE= FLASK_DEBUG=0
.venv/bin/python -m flask --app run mail-status
```

`mail-status` imprime flags y presencia de host/remitente/credenciales, nunca sus
contenidos. Confirmar `smtp`, correo y verificación activos, recovery y orders
apagados. No usar el fixture fake de navegador para correo real.

### Comprobar SMTP sin enviar

Con ese mismo entorno:

```bash
.venv/bin/python -m flask --app run smtp-check
```

Solo conecta, negocia TLS y autentica. No ejecuta MAIL, RCPT o DATA y no genera
correo ni tokens. Debe terminar en `SMTP_AUTH_OK (sin envío)`. Los fallos muestran
solo categorías fijas: `certificate_verification`, `authentication`, `connection`,
`sender_refused`, `recipient_refused`, `message_rejected` o `transport`. No se
imprimen excepciones crudas, respuestas del servidor, claves ni destinatarios.

### Una sola verificación real

Primero ejecutar todas las suites fake/mock. Luego, con el entorno anterior y
solo si el archivo DB indicado todavía no existe:

```bash
.venv/bin/python -m flask --app run init-db
.venv/bin/python -m flask --app run run --host 127.0.0.1 --port 5003 --no-reload
```

1. Registrar una cuenta nueva con un buzón del desarrollador autorizado. No usar
   clientes reales. No es necesario importar catálogo ni crear pedidos/admin.
2. Esperar un solo correo. No reenviar ni repetir el registro para diagnosticar.
   Los logs INFO indican token creado, intento SMTP y aceptación; no contienen
   el token, URL, credenciales, cuerpo ni dirección. Un error muestra categoría
   segura y la pantalla informa el fallo sin destruir la cuenta.
3. Confirmar el evento en Brevo → Transactional → Logs y recepción en el buzón,
   incluido spam. `delivery accepted` significa aceptación SMTP, no recepción.
4. Abrir el enlace desde el mismo equipo y confirmar el formulario. GET permite
   ver la página; POST con CSRF marca el correo como verificado. No copiar el
   enlace en terminales, informes ni capturas. Un segundo uso debe fallar.
5. Conservar el servidor local mientras se confirma el enlace, luego detenerlo.
   Mantener recovery y order emails apagados; probarlos únicamente con fake/mock.

No ejecutar `retry-order-mail` durante esta prueba: actúa sobre pendientes de
pedidos de la DB seleccionada. SMTP puede aceptar un correo aunque se pierda la
respuesta; no reintentar a ciegas. Registrar solo resultado y fecha, sin secretos.

## Desarrollo, staging y producción

Desarrollo habitual sigue funcionando sin SMTP con los cuatro interruptores en
false. En staging/production usar variables del servicio o un archivo privado
de nombre propio; no dependen de `.env.smtp-manual`. Requieren SECRET_KEY robusta,
DB propia y, con correo activo, PUBLIC_BASE_URL HTTPS y TLS/SSL válido. No aceptan
backend fake. Con todo apagado pueden arrancar sin correo.

Cada feature se controla por su flag y requiere transporte disponible. Para
apagado total poner MAIL_ENABLED y las tres features en false y reiniciar.
Apagar no elimina tokens ni cola. No se hace deploy, dominio ni migración de DB.

## Pruebas y límites de evidencia

Las suites existentes cubren fake, expiración, uso único, CSRF, throttling,
recuperación, notificaciones y reintentos. Las nuevas regresiones comprueban
archivo explícito, precedencia del entorno, archivo ausente, SMTP en registro,
un solo envío, cuenta preservada ante fallo, TLS verificado y ausencia de secretos
en logs/CLI. Los tests SMTP usan mocks y nunca deben recibir credenciales reales.
Los fixtures de navegador usan DB aislada y backend fake.

Ejecutar Python completo, JS storage/admin, customer E2E con `--email-e2e`,
commercial browser y public browser (este último con fixture `BROWSER_PUBLIC_ONLY=1`),
con artefactos fuera de Git. Terminar con `git diff --check`. No commit/push si
falla una suite importante. Recepción y evento Brevo requieren evidencia del buzón
/panel; autenticación por sí sola no los acredita.

### Evidencia de esta intervención

- Reproducción HTTP con DB nueva y transporte mock: sin selección privada,
  HTTP 302 / 1 cuenta / 0 tokens / 0 conexiones; con selección privada,
  HTTP 302 / 1 cuenta / 1 token / 1 conexión / 1 mensaje.
- `smtp-check` ejecutado contra el host privado con red autorizada:
  `SMTP_AUTH_OK (sin envío)`, TLS verificado. El sandbox sin acceso de red había
  devuelto la categoría segura `connection`.
- Prueba de entrega real pendiente de identificar un destinatario controlado y
  confirmar recepción/evento Brevo; no se confunde autenticación con entrega.

Validación completada: 205 tests Python, JS storage/admin, 43 customer E2E,
69 commercial browser y 89 public browser. `git diff --check` correcto.
El hash de `instance/tienda.db` no cambió. No hubo envío real de mensajes.
