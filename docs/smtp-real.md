# Configurar SMTP real sin publicar la aplicación

Estado: procedimiento preparado; entrega real pendiente de credenciales y ejecución
manual. No se activa correo por instalar estos cambios. El transporte existente
`app/services/mail.py` y la lectura de `config.py` no necesitan cambios.

## 1. Proveedor de referencia

Se propone **Brevo**; no hay una cuenta/proveedor confirmado para este proyecto.
En Settings → SMTP & API → SMTP, copiar el **SMTP login** y generar una clave
SMTP dedicada a esta prueba, con vencimiento. Guardarla en un gestor de secretos.
No usar la contraseña de la cuenta ni una API key. Para otros proveedores que
exijan contraseña de aplicación/token, nunca usar la contraseña normal.

Registrar y verificar el remitente en el proveedor y completar la autenticación
DNS del dominio que indique su panel (DKIM y política DMARC; SPF según proveedor,
sin crear registros SPF duplicados). Verificar que permite correo transaccional,
el destinatario de prueba y la cuota necesaria antes de activar.

Referencias oficiales consultadas el 2026-09-14:
[relay SMTP](https://help.brevo.com/hc/en-us/articles/7924908994450-Send-transactional-emails-using-Brevo-SMTP),
[claves SMTP](https://help.brevo.com/hc/en-us/articles/7959631848850-Create-and-manage-your-SMTP-keys).

## 2. Variables exactas

| Variable | Valor para la prueba / significado |
|---|---|
| `MAIL_ENABLED` | `false` al preparar; `true` al iniciar la prueba manual |
| `MAIL_BACKEND` | `smtp`; `fake` solo para pruebas automatizadas/locales |
| `SMTP_HOST` | `smtp-relay.brevo.com` para Brevo |
| `SMTP_PORT` | `465` en este procedimiento |
| `SMTP_USERNAME` | SMTP login del panel; no asumir que es el correo de la cuenta |
| `SMTP_PASSWORD` | Clave SMTP dedicada, solo en archivo privado/gestor de secretos |
| `SMTP_USE_TLS` | `false` con 465; significa STARTTLS en este código |
| `SMTP_USE_SSL` | `true` con 465; TLS desde el inicio de la conexión |
| `MAIL_FROM_ADDRESS` | Dirección real verificada por el proveedor |
| `MAIL_FROM_NAME` | `Yoli Figuras de Fomix` (puede añadir «PRUEBA») |
| `PUBLIC_BASE_URL` | Local: `http://127.0.0.1:5003`; staging/production: origen HTTPS real |
| `EMAIL_VERIFICATION_ENABLED` | `false` al preparar; `true` para verificación |
| `ACCOUNT_RECOVERY_ENABLED` | `false` al preparar; `true` para recuperación |
| `ORDER_EMAIL_NOTIFICATIONS_ENABLED` | `false` al preparar; `true` para confirmación y estado |

Alternativa si el proveedor ofrece STARTTLS: puerto `587`, TLS `true`, SSL `false`.
Nunca activar ambos. El código admite credenciales vacías solo si ambas están
vacías (relay sin autenticación); el proveedor propuesto requiere ambas.
`EMAIL_VERIFICATION_LIFETIME_HOURS=24` y `ACCOUNT_RECOVERY_LIFETIME_HOURS=1`
son opcionales, aceptan enteros de 1 a 168.

## 3. Crear el archivo privado y aislar los datos

Antes de activar, desde la raíz:

```bash
git status --short --branch
git fetch origin
git rev-list --left-right --count main...origin/main
```

Continuar con rama `main`, árbol limpio y resultado `0 0`. Si hay divergencias,
resolverlas antes de probar; no hacer reset ni sobrescribir trabajo.

La prueba usa una **base nueva**, no una copia comercial (que podría contener
notificaciones pendientes para clientes reales). No requiere respaldo de
`instance/tienda.db` porque no se utiliza. Si en otra intervención fuera
imprescindible escribir una DB existente, primero ejecutar `flask --app run
backup-db` con el entorno de esa DB y el correo apagado; verificar el respaldo.
Para PostgreSQL seguir `docs/production-backup.md`.

Crear un archivo exclusivo sin sobrescribir uno existente:

```bash
(umask 077; cp -n .env.example .env.smtp-manual)
chmod 600 .env.smtp-manual
git check-ignore .env .env.smtp-manual
```

Editar `.env.smtp-manual` en un editor local. Introducir los valores de la tabla
manteniendo los cuatro interruptores en `false`. Además configurar:

```dotenv
APP_ENV=development
DATABASE_URL=sqlite:////home/kevin/Documentos/figuras-yoli/instance/smtp-manual.db
PUBLIC_BASE_URL=http://127.0.0.1:5003
SESSION_COOKIE_SECURE=0
BEHIND_PROXY=0
HSTS_ENABLED=0
TRUSTED_HOSTS=127.0.0.1
LOG_LEVEL=WARNING
FLASK_DEBUG=0
```

Eliminar comentarios al final de valores: el cargador mínimo no los elimina.
Admite comillas exteriores, pero no expansión `${VARIABLE}` ni secretos multilínea.
No usar `source`, `set -x`, `printenv`, volcado de configuración, depuración SMTP,
capturas del archivo o secretos en argumentos/historial. No imprimir SMTP_PASSWORD.
`.env` y `.env.*` están ignorados; nunca usar `git add -f` sobre ellos.

La aplicación carga automáticamente solo `.env`, y las variables del proceso
prevalecen. Para no tocar el `.env` habitual, abrir una terminal nueva y ejecutar
este lanzador interactivo: carga el archivo privado y permite únicamente las
operaciones indicadas. No imprime configuración ni credenciales.

```bash
.venv/bin/python - <<'PY'
import os
from pathlib import Path
from config import _load_dotenv
# Terminal dedicada: evita heredar valores de otro entorno.
for key in list(os.environ):
    if key.startswith(('SMTP_', 'MAIL_', 'EMAIL_VERIFICATION_', 'ACCOUNT_RECOVERY_', 'ORDER_EMAIL_')) or key in ('APP_ENV', 'DATABASE_URL', 'PUBLIC_BASE_URL'):
        os.environ.pop(key)
_load_dotenv(Path('.env.smtp-manual'))
expected = 'sqlite:////home/kevin/Documentos/figuras-yoli/instance/smtp-manual.db'
assert os.environ.get('DATABASE_URL') == expected, 'DB de prueba incorrecta'
assert os.environ.get('APP_ENV') == 'development', 'Entorno incorrecto'
from app import create_app
app = create_app()
# El heredoc ocupa stdin; recuperar el terminal para los prompts interactivos.
import sys
sys.stdin = open('/dev/tty')
choice = input('Operación: init-db / import-catalog / create-user / serve: ')
if choice == 'serve':
    app.run(host='127.0.0.1', port=5003, debug=False, use_reloader=False)
elif choice in ('init-db', 'import-catalog', 'create-user'):
    if choice == 'init-db':
        assert not Path('instance/smtp-manual.db').exists(), 'Use una DB nueva'
    args = [choice, 'data/catalog_seed.csv', '--reviewed'] if choice == 'import-catalog' else [choice]
    app.cli.main(args=args, prog_name='smtp-manual', standalone_mode=False)
else:
    raise SystemExit('Operación no permitida')
PY
```

Ejecutar el bloque tres veces: `init-db`, `import-catalog`, `create-user`.
Crear un administrador ficticio mediante el prompt de contraseña sin eco.
No ejecutar fixtures de navegador para enviar correo real. No programar reintentos.

## 4. Una sesión manual real: cuatro correos

1. Editar el archivo privado: activar `MAIL_ENABLED` y las tres features.
   Ejecutar el lanzador y elegir `serve`. Usar solo este equipo y
   `http://127.0.0.1:5003`; los enlaces locales deben abrirse en el mismo equipo.
   No hace falta dominio público, túnel, deploy ni publicación.
2. **Verificación:** registrar una cuenta nueva con un buzón de prueba controlado
   por quien ejecuta la prueba. Abrir el único correo y verificar la cuenta.
   Confirmar «verificado» en el panel. No pulsar reenviar.
3. **Recuperación:** cerrar sesión, solicitar recuperación una vez para esa
   cuenta, abrir el enlace y cambiar a otra contraseña de prueba. Comprobar que
   la anterior falla y que la nueva permite entrar.
4. **Confirmación:** añadir un producto del catálogo, cantidad 1, y crear una
   única solicitud marcada «PRUEBA SMTP — NO PRODUCIR» en su observación.
   Comprobar un correo con número de solicitud, estado y cantidades correctas,
   sin datos internos. No generar cotización, factura ni producción.
5. **Cambio de estado:** entrar con el administrador ficticio y cambiar esa
   solicitud una sola vez de pendiente a en proceso. Confirmar un correo nuevo.
   Guardar el mismo estado otra vez debe producir cero correos adicionales.
6. Registrar únicamente fecha, proveedor, tipo y resultado recibido/no recibido;
   nunca tokens, contraseñas, enlaces completos ni cuerpos. Resultado esperado:
   cuatro correos en total. Revisar spam y panel del proveedor si falta alguno.
7. Detener con Ctrl+C, apagar los cuatro interruptores en el archivo y revocar
   la clave SMTP de prueba. Conservar o retirar la DB desechable según necesidad;
   no mezclarla con la DB comercial. Reabrir desarrollo con su configuración usual.

Si falla un envío, detener la sesión y revisar host/puerto/cifrado, login, clave,
remitente, cuota y conectividad sin revelar secretos. No reintentar toda la
sesión a ciegas: SMTP puede aceptar un mensaje aunque se pierda la respuesta.
`retry-order-mail` reintenta pendientes de la base seleccionada y puede enviar
varios; no ejecutarlo sobre una DB comercial como parte de esta prueba.

## 5. Staging/production y control de features

Preparar un `.env` privado independiente en cada entorno, con permisos 600,
`APP_ENV=staging` o `production`, `SECRET_KEY` aleatoria de al menos 32 caracteres,
DB propia y `PUBLIC_BASE_URL=https://dominio-real` sin ruta, credenciales, query
ni fragmento. Configurar cookies seguras y proxy conforme a `docs/deployment.md`.
No reutilizar la clave SMTP de prueba. Esto se prepara para una activación futura;
no ejecutar deploy en este procedimiento.

- Verificación: `EMAIL_VERIFICATION_ENABLED=true/false`.
- Recuperación: `ACCOUNT_RECOVERY_ENABLED=true/false`.
- Confirmación y cambios de estado juntos: `ORDER_EMAIL_NOTIFICATIONS_ENABLED=true/false`.
- Apagado total: poner **las tres features y MAIL_ENABLED en false** y reiniciar.
- Activación: SMTP válido, `MAIL_ENABLED=true`, features deseadas en `true`, reiniciar.

Staging/production rechaza `fake`, features activas con transporte apagado,
SMTP activo sin cifrado y base pública sin HTTPS si el correo está activo.
Puede arrancar con todo el correo apagado. Cambiar un archivo no modifica un
proceso que ya está arrancado: reiniciar es obligatorio. Apagar una feature no
borra tokens ni la cola; al reactivarla pueden seguir existiendo pendientes.

## 6. Validación automatizada sin envío

Ejecutar la suite con lectura de `.env` anulada, entorno de correo limpio y
conexiones SMTP bloqueadas. Los casos de correo usan `fake`; los casos del
transporte usan mocks (nunca red):

```bash
.venv/bin/python - <<'PY'
import os
import unittest
from unittest.mock import patch
for key in list(os.environ):
    if key.startswith(('SMTP_', 'MAIL_', 'EMAIL_VERIFICATION_', 'ACCOUNT_RECOVERY_', 'ORDER_EMAIL_')):
        os.environ.pop(key)
os.environ['APP_ENV'] = 'development'
with patch('config._load_dotenv'), patch('smtplib.SMTP', side_effect=AssertionError('SMTP real bloqueado')), patch('smtplib.SMTP_SSL', side_effect=AssertionError('SMTP real bloqueado')):
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests'))
raise SystemExit(not result.wasSuccessful())
PY
node --test tests/test_storage.cjs tests/test_admin_js.cjs
git diff --check
git status --short --branch
```

La suite no acredita entrega real: solo la recepción manual de los cuatro mensajes
la confirma. Riesgos restantes: rechazo/spam, cuota del proveedor, puertos bloqueados,
URL incorrecta, secretos expuestos por herramientas externas, datos personales en
el proveedor y duplicados ante respuesta SMTP incierta. No registrar URLs con
tokens en proxies, terminales ni capturas. Nunca desactivar validación de certificados.
