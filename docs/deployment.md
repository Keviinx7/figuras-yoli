# Despliegue — Yoli Figuras de Fomix

Guía para preparar una futura puesta en producción pública. **La tienda aún no
está desplegada.** Todo lo que sigue describe el plan seguro y los comandos que
se usarán cuando se autorice el despliegue real; nada de esto se ha ejecutado en
un servidor.

## Principios

- Cero información comercial inventada: precios, stock, envíos, sucursales y
  disponibilidad se confirman por WhatsApp. La web nunca inventa datos.
- La base de datos local (`instance/tienda.db`) y las imágenes verificadas son
  el único origen de catálogo. **No se reimporta el PDF ni se reemplaza la base.**
- Toda escritura administrativa pasa por el panel con roles `admin`/`vendedor`;
  el consentimiento del cliente se registra por separado, no por la web.
- Las claves y secretos solo viven en el entorno del servidor, nunca en Git.

## Entornos

La configuración se resuelve por variable de entorno en tiempo de arranque
(`config.py`, `get_config()`). `APP_ENV` elige el entorno; también se acepta
`FLASK_ENV` y `YOLI_ENV` por compatibilidad.

| Entorno | Uso                             | SECRET_KEY                     | Cookies Secure | Debug |
|---------|---------------------------------|--------------------------------|----------------|-------|
| development | Trabajo local                | opcional (auto en `.session_key`) | no          | sí    |
| testing | Pruebas automatizadas            | la que pasen los tests         | no             | no    |
| staging | Réplica previa a producción      | requerida, ≥32 caracteres      | solo con HTTPS | no    |
| production | Público                      | requerida, ≥32 caracteres      | sí             | no    |

Variables relevantes: ver `.env.example` (el archivo se copia como `.env` solo
en el servidor; en desarrollo ya funciona sin `.env`).

`get_config()` rechaza valores inválidos (entorno desconocido, `SECRET_KEY`
débil en staging/production) con un error claro en el arranque.

## Prepare el entorno de staging (recomendado)

1. Réplica aislada del catálogo en `staging/` o una copia de `instance/tienda.db`
   como base de pruebas (nunca usar la base real con datos ficticios).
2. Instalar dependencias base:

   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   ```

   Si `DATABASE_URL` apunta a PostgreSQL: `pip install -r requirements-postgres.txt`.
3. Copiar `.env.example` a `.env` y fijar `APP_ENV=staging`, `SECRET_KEY`
   (generar con `python -c "import secrets; print(secrets.token_hex(32))"`),
   `BEHIND_PROXY=1`, `HSTS_ENABLED=0` hasta tener certificado, `TRUSTED_HOSTS`.
4. Ejecutar `backup-db` antes de cualquier operación sobre datos reales.

## Ejecución WSGI

Gunicorn sirve `wsgi:app`. Workers hay que ajustarlos a la memoria de la VM;
2 procesos × 2 hilos es prudente para una tienda-catálogo pequeña. Con SQLite,
**un solo proceso** es lo más seguro para evitar contención de escritura; con
PostgreSQL se pueden subir workers sin riesgo.

```bash
.venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 2 --threads 2 --timeout 30 wsgi:app
```

La app escucha solo en loopback; Nginx termina el tráfico externo.

## Base de datos

### SQLite (estado actual)

- Es la base operativa real; respaldar con `backup-db` antes de cualquier cambio.
- `upgrade-db` añade tablas comerciales de forma aditiva y verificada; nunca
  reimporta productos y solo funciona sobre SQLite local.

### PostgreSQL (fase futura, cuando se autorice)

- `requirements-postgres.txt` instala el driver `psycopg`. No está en
  `requirements.txt` porque hoy no se usa.
- El código es portabble por diseño: el upsert de numeración
  (`documents.next_number`), la serialización de escritura (`BEGIN IMMEDIATE` en
  login y `staff_only`) y la búsqueda (`search_normalize`) detectan el dialecto
  de la base y no dependen de SQLite. La búsqueda usará `ILIKE` con patrón
  escapado, y las escrituras concurrentes usarán el aislamiento de PostgreSQL.
- **Migraciones de esquema:** cuando exista una base PostgreSQL con datos reales
  se introducirá Alembic. No se agrega todavía para no añadir un nivel de
  complejidad al despliegue actual ni competir con `upgrade-db`. Estrategia:
  1. `alembic init` con un historial limpio que refleje el esquema vigente
     (`db.create_all()` como base de comparación).
  2. Cada cambio de esquema = una migración por revisión, revisada, con `downgrade`.
  3. Los datos reales nunca se reimportan; las migraciones son aditivas o con
     copias de respaldo previas verificadas (mismo criterio que `upgrade-db`).
  4. Probar primero en staging y respaldar antes de aplicar en producción.

## HTTPS, Nginx y systemd

Ver archivos de ejemplo en `deploy/`:

- `deploy/nginx-yoli.conf.example`: TLS (certificados Let's Encrypt emitidos con
  `certbot --nginx -d example.com -d www.example.com`), proxy a Gunicorn con
  `X-Forwarded-Proto`, `client_max_body_size 64k` y `/health` para los sondeos.
- `deploy/yoli.service.example`: unidad systemd con `EnvironmentFile` apuntando
  a `/etc/yoli/yoli.env` (fuera de Git), `NoNewPrivileges`, reinicio automático.

Pasos al autorizar el despliegue:

```bash
sudo apt update && sudo apt install nginx certbot python3-certbot-nginx
sudo mkdir -p /etc/yoli
sudo cp /root/yoli.env /etc/yoli/yoli.env && sudo chmod 600 /etc/yoli/yoli.env
sudo cp deploy/yoli.service.example /etc/systemd/system/yoli.service  # editar usuario/rutas/entorno
sudo systemctl daemon-reload && sudo systemctl enable --now yoli
sudo cp deploy/nginx-yoli.conf.example /etc/nginx/sites-available/yoli
sudo ln -s /etc/nginx/sites-available/yoli /etc/nginx/sites-enabled/yoli
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d example.com -d www.example.com
```

Solo cuando el certificado exista, activar `HSTS_ENABLED=1` y recargar.

## Correo a clientes

El portal puede verificar correos, enviar recuperación de contraseña y
notificar solicitudes/cambios de estado. Todo esto es opcional y **debe estar
apagado hasta tener un remitente real**. Detalles en
[docs/email-clientes.md](email-clientes.md).

Al autorizar el correo en staging/production:

1. Fijar en `/etc/yoli/yoli.env`: `MAIL_ENABLED=1`, `MAIL_BACKEND=smtp`,
   `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
   (ambas o ninguna), `SMTP_USE_TLS`/`SMTP_USE_SSL` (nunca ambas),
   `MAIL_FROM_ADDRESS`, `MAIL_FROM_NAME`.
2. `PUBLIC_BASE_URL=https://tienda.example` es **obligatoria y https** en
   staging/production: los enlaces de verificación/reset se construyen con esa
   base, nunca con el `Host` del navegador. El arranque la valida y aborta con
   un error claro si falta o es inválida.
3. Activar solo los flujos necesarios:
   `EMAIL_VERIFICATION_ENABLED`, `ACCOUNT_RECOVERY_ENABLED`,
   `ORDER_EMAIL_NOTIFICATIONS_ENABLED`. Con SMTP sin configurar estas flags
   hacen que el arranque falle en producción (por diseño).
4. Un fallo de entrega **no borra ni revierte** pedidos/solicitudes: la fila
   queda pendiente en `order_email_outbox` y se reintenta con
   `.venv/bin/flask retry-order-mail` (también se reintenta en el siguiente
   cambio de estado). No hay Redis/Celery.
5. `deploy/nginx-yoli.conf.example` y `deploy/yoli.service.example` apagan el
   registro de rutas para que las URLs con token portador no queden en logs;
   los tokens tampoco se imprimen en la app ni se muestran al admin.

Secretos: SMTP y `SECRET_KEY` solo en el `.env` del servidor; nunca en Git,
logs, documentación ni capturas.

## Verificación del despliegue

- `curl -fsS https://example.com/health` → `{"database":"ok","status":"ok"}`.
- `curl -I` de la portada: cabeceras de seguridad presentes
  (`X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`,
  `Permissions-Policy`, `Content-Security-Policy`, `Strict-Transport-Security`
  solo bajo HTTPS).
- Sin `TRUSTED_HOSTS`, un Host desconocido responde 400.
- Prueba real de pedido vacío y de panel con usuario creado por `create-user`.

## Qué no se hace en el despliegue

- No se publican precios, medidas, stock ni disponibilidad no confirmados.
- No hay pagos online ni facturación electrónica (SRI) integrados; el flujo de
  cotización/factura queda dentro del panel para documentación interna.
- No se ponen límites automáticos de venta ni inventario en la web pública.
- La clave de sesión de desarrollo (`instance/.session_key`) no pasa al servidor.