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
  automáticamente (flag `EMAIL_VERIFICATION_ENABLED`, default `False`).
- **Recuperación honesta**: `ACCOUNT_RECOVERY_ENABLED` (default `False`).
  Sin un remitente SMTP configurado el sitio no finge haber enviado un
  correo: orienta al cliente a escribir por WhatsApp (ver `recover()`).

## Rutas

Portal (`app/portal/routes.py`, blueprint `portal`):

`/registro`, `/cuenta/login`, `/cuenta` (panel), `/cuenta/perfil`,
`/cuenta/pedidos`, `/cuenta/pedido/<id>`, `/cuenta/recuperar`,
`/cuenta/recuperar/<token>`, `/cuenta/logout`.

Administración (`app/requests_admin/routes.py`, blueprint `requests_admin`,
prefijo `/admin/pedidos`, sólo staff):

`/`, `/admin/pedidos/<id>`, `/admin/pedidos/<id>/estado`,
`/admin/pedidos/clientes/<id>/cuenta` (toggle `is_active`, sólo admin; nunca
toca contraseñas y rota `session_token` al desactivar).

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
- `tests/browser_customer.mjs` (32 checks en Chrome headless): registro,
  carrito → pedido persistido, edición de perfil, logout/login, cierre del
  portal tras logout, cierre de `/admin` para cliente, cambio de estado por
  staff y seguimiento por el cliente; viewports 1440/768/390/320.
- Suite existente intacta: 159 Python, 11 storage, 6 admin JS, 89 + 69
  browser checks.

## Configuración

`config.py` (flags, todos con default `False` para no cambiar el
comportamiento actual):

- `ACCOUNT_RECOVERY_ENABLED`
- `ACCOUNT_RECOVERY_LIFETIME_HOURS` (default `1`)
- `EMAIL_VERIFICATION_ENABLED`

`tests/test_production.py` comprueba que los tres existan y preserven sus
defaults.