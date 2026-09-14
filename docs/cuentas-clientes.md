# Cuentas de clientes: portal y pedidos persistidos

Feature añadida a la tienda pública: los clientes pueden crear una cuenta,
guardar sus solicitudes de cotización en su cuenta y hacerles seguimiento,
sin que eso mezcle identidades con el equipo (`/admin`) ni revele precios,
costos o márgenes.

## Decisión central

El registro de un cliente NUNCA crea un usuario del personal (`users`). La
tienda conserva dos identidades totalmente separadas:

- **Staff** (`users` + `LoginManager`, sesión `_user_id`): panel `/admin`.
- **Cliente** (`customer_accounts`, sesión propia): portal `/cuenta` y
  `/registro`, más pedidos en `/cuenta/pedidos`.

Las dos sesiones no conviven en el mismo navegador: `account_login()`
ejecuta `logout_user()` y reemplaza limpiamente la sesión, y el login del
staff hace `session.clear()`. Empezar sesión en el portal invalida cualquier
sesión del personal activa, y viceversa (verificado en
`test_admin_session_never_reaches_portal` y `test_customer_never_reaches_admin`).

## Modelos (tablas nuevas)

`app/models/customer_account.py`:

- **`customer_accounts`**: cuenta del cliente (correo único, hash scrypt,
  `is_active`, `email_verified`, `session_token` rotado en cada
  login/registro/cambio de contraseña, `last_login`).
- **`customer_requests`**: solicitud persistida con estado
  (`pending`, `processing`, `completed`, `rejected`), modalidad de entrega,
  snapshot del cliente (`customer_snapshot` JSON) y notas.
- **`customer_request_items`**: líneas con SNAPSHOT del producto
  (código, nombre, cantidad, tamaño, personalización). Usa
  `product_code_snapshot`/`product_name_snapshot` para que el historial de
  solicitudes no cambie si el catálogo se edita.

Estas tres tablas se crean de forma aditiva al migrar: `db.create_all()`
sobre `instance/tienda.db` NO toca ninguna tabla existente.

El correo añade además (ver `docs/email-clientes.md`):

- **`account_email_tokens`**: digests SHA-256 de tokens de verificación y
  recuperación (expiración, un solo uso, propósito y credencial ligada).
- **`email_rate_limits`**: contadores atómicos por IP e identidad.
- **`order_email_outbox`**: cola durable de confirmaciones/cambios de estado;
  la fila vive en la misma transacción que el pedido y se entrega tras commit.

### Nada económico se guarda

Las tablas nuevas no tienen columnas de precios, costos ni márgenes. El
portal jamás registra `total`, `subtotal`, `unit_price`, `unit_cost` ni
`cost_snapshot` (lo comprueban
`test_request_persists_without_prices_or_costs` y el E2E
`tests/browser_customer.mjs`). Cualquier valor de montos llegado del
formulario del carrito es ignorado por el backend.

## Seguridad

- **Validación back-end completa**: `save_customer_request` revalida el
  carrito contra `validate_cart()` y `public_products()`; los precios del
  formulario jamás se leen. Códigos no publicados → error.
- **CSRF** en todos los POST (`protect_post` global con `X-CSRF-Token`).
- **IDOR**: `/cuenta/pedido/<id>` solo resuelve solicitudes del cliente
  autenticado (`first_or_404`).
- **Login genérico**: "Correo o contraseña incorrectos" indistintamente para
  correo inexistente o contraseña mala; mismo texto de error.
- **Rate limit por IP**: reutiliza `LoginAttempt` (10 fallos / 15 minutos →
  429).
- **Verificación de correo**: `email_verified` nunca se activa
  automáticamente (flag `EMAIL_VERIFICATION_ENABLED`, default `False`). Cuando
  el flag y un transporte SMTP están activos, el registro/envío envía un enlace
  temporal de un solo uso; en caso contrario el portal funciona igual y avisa
  por WhatsApp.
- **Recuperación**: `ACCOUNT_RECOVERY_ENABLED` (default `False`). Sin un
  remitente SMTP configurado el sitio no finge haber enviado un correo: orienta
  al cliente a escribir por WhatsApp (ver `recover()`). Con SMTP activo envía
  un enlace de un solo uso que rota la contraseña y anula sesiones y enlaces
  anteriores. Los tokens se guardan solo como digest, caducan y se revocan al
  desactivar la cuenta o cambiar el correo.

## Rutas

Portal (`app/portal/routes.py`, blueprint `portal`):

`/registro`, `/cuenta/login`, `/cuenta` (panel), `/cuenta/perfil`,
`/cuenta/pedidos`, `/cuenta/pedido/<id>`, `/cuenta/recuperar`
(también `/cuenta/olvide-contrasena`), `/cuenta/recuperar/<token>`
(también `/cuenta/restablecer/<token>`), `/cuenta/verificacion-pendiente`,
`/cuenta/verificar/<token>`, `/cuenta/reenviar-verificacion`,
`/cuenta/logout`. El perfil permite cambiar el correo confirmando la
contraseña actual; al cambiar, se invalidan los enlaces anteriores y se
pide una nueva verificación. Las rutas de verificación/recuperación
responden 404 cuando su flag está apagado.

Administración (`app/requests_admin/routes.py`, blueprint `requests_admin`,
prefijo `/admin/pedidos`, sólo staff):

`/`, `/admin/pedidos/<id>`, `/admin/pedidos/<id>/estado`,
`/admin/pedidos/clientes/<id>/cuenta` (toggle `is_active`, sólo admin; nunca
toca contraseñas, rota `session_token` y revoca los enlaces pendientes al
desactivar; reactivar no revive enlaces antiguos). El cambio real de estado
encola una notificación de correo; guardar el mismo estado no duplica envíos.

## Flujo del carrito

`app/templates/public/cart.html` muestra dos ramas:

- **Autenticado**: formulario a `portal.submit_request` (entrega + notas);
  el botón publica la solicitud y redirige a `/cuenta/pedido/<id>`.
- **Anónimo**: se conserva el flujo WhatsApp existente
  (`orders.preview`) con la nota de que puede crear cuenta para guardar y
  hacer seguimiento. `cart.js` no cambió: usa el mismo
  `#quote-submit` / `#cart-payload`.

Se mantuvo intacto el envío anónimo por WhatsApp; la vía persistente
simplemente exige cuenta para no "robar" clientes al canal actual.

## Notas de implementación

- El ticket en Jinja es `'%04d'|format(req.id)` (formato `%`).
- `session.permanent = True` mantiene la sesión del cliente (cookie
  `HttpOnly`, `SameSite=Lax`, `no-store` como el resto del portal).
- `CustomerRequestItem.request` usa `overlaps="items"` para evitar el
  warning de SQLAlchemy en mappers.
- El fixture `tests/browser_commercial_server.py` garantiza un producto
  público personalizable (`FY.EZE.777`) para el E2E del portal; no siembra
  datos en `tienda.db`.

## Cobertura

- `tests/test_customer_portal.py` (23 casos): registro, sesión, login,
  rate-limit, logout, separación staff/cliente en ambos sentidos, CSRF en
  todas las rutas, pedidos persistidos sin precios, IDOR, perfil,
  recuperación honesta.
- `tests/test_customer_email.py` (hereda `PortalTests` + casos propios):
  ciclo de vida de verificación/reenvío, expiración, propósito, revocación
  por desactivación/reactivación, recuperación genérica, rate-limit,
  E2E HTTP completo de verificación → pedido → estado → recuperación,
  cambio de correo sin apropiación de cuentas, fallo SMTP que preserva el
  pedido y reintenta, host-header poisoning, enmascarado de tokens en logs,
  validación de configuración de producción y consumo atómico.
- `tests/browser_customer.mjs` (36 checks en Chrome headless contra el
  fixture de correo fake, `--email-e2e`): registro → verificación por correo
  fake → login → carrito → solicitud → confirmación por correo fake →
  cambio de estado del admin → un solo correo por cambio real → seguimiento
  del cliente; olvidé contraseña → reset → la anterior falla → la nueva
  funciona; viewports 1440/768/390/320.
- Suite existente intacta: 195 Python, 11 storage, 6 admin JS, 89 + 69
  browser checks (`test_customer_email.py` ya incluye los 23 de portal).

## Configuración

`config.py` (flags, todos con default `False` para no cambiar el
comportamiento actual):

- `ACCOUNT_RECOVERY_ENABLED`
- `ACCOUNT_RECOVERY_LIFETIME_HOURS` (default `1`)
- `EMAIL_VERIFICATION_ENABLED`
- `EMAIL_VERIFICATION_LIFETIME_HOURS` (default `24`)
- `ORDER_EMAIL_NOTIFICATIONS_ENABLED`

Y transporte en `config.py` + `.env.example`: `MAIL_ENABLED`, `MAIL_BACKEND`,
`SMTP_*`, `MAIL_FROM_*`, `PUBLIC_BASE_URL`. En producción el arranque exige
SMTP real y `PUBLIC_BASE_URL` https (ver `docs/email-clientes.md`).

`tests/test_production.py` comprueba que los flags originales existan y
preserven sus defaults.