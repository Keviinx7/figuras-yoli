# Yoli Figuras de Fomix

Tienda de catálogo y solicitudes de cotización con Flask, Flask-SQLAlchemy, SQLite, Jinja2, HTML, CSS y JavaScript vanilla. Los precios, disponibilidad y envío se confirman con el negocio por WhatsApp.

## Ejecutar localmente

Desde el directorio del proyecto, usando el entorno virtual existente:

```bash
cd /home/kevin/Documentos/figuras-yoli
.venv/bin/python -m flask --app run init-db
.venv/bin/python run.py
```

Abrir **http://127.0.0.1:5000/**. `init-db` puede repetirse: crea las tablas que faltan y las categorías de referencia sin borrar productos. No actualiza esquemas existentes.

En una instalación nueva, crear primero el entorno e instalar las dependencias:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

El servidor de `run.py` es para desarrollo local. Para un despliegue real use
`wsgi.py` con Gunicorn, Nginx con HTTPS y las variables de entorno descritas en
`.env.example`; la guía completa está en [docs/deployment.md](docs/deployment.md)
y los respaldos en [docs/production-backup.md](docs/production-backup.md).
La tienda aún no se ha desplegado: la configuración por entorno, la seguridad
web y los comandos de respaldo están preparados, pero el servidor público no
existe.

## Estado del catálogo

**PDF revisado: 33 páginas; 173 productos importados con imágenes en SQLite.**

`data/catalog_seed.csv` contiene 173 códigos reales, conservando Ñ y ceros iniciales. Se verificaron 17 categorías. Hay nueve carátulas fotografiadas sin código, pendientes de identificación y fuera de la importación. Se excluyeron 77 casillas .000 y 20 casillas con logotipo y códigos no nulos en las plantillas finales. Los datos ficticios de pruebas solo existen en bases temporales aisladas. Véase [el informe completo](docs/revision-implementacion.md) y [el manifiesto por página y casilla](docs/catalog-audit/manifest.json).

### Nombres descriptivos revisados

Se revisaron las 173 imágenes: 149 nombres añadidos, un nombre erróneo corregido y 22 conservados. Hay 172 fichas con nombre; FY.VAR.019 permanece pendiente por imagen anatómica ambigua. Las nueve carátulas siguen sin código comercial y fuera de SQLite.

El registro completo está en [docs/name-review/report.md](docs/name-review/report.md); `data/catalog_names.json` conserva los nombres revisados para futuras reproducciones del CSV. **No es necesario volver a extraer ni importar el PDF.** `.venv/bin/python -m scripts.update_catalog_names` actualiza únicamente nombres y textos alternativos de imágenes existentes, verifica coincidencia exacta de códigos, crea una copia previa y utiliza una transacción. No crea productos ni modifica códigos, categorías, rutas o imágenes.

### Flujo de preparación e importación

1. Colocar el PDF auténtico en `docs/catalogo-productos.pdf`.
2. Revisar visualmente cada página y registrar categorías, códigos, nombres explícitos e imágenes reales. Identificar espacios vacíos e imágenes institucionales.
3. Excluir todos los códigos terminados en `000`. Los nombres descriptivos pueden basarse en evidencia visual revisada; registrar la decisión y conservar el código si la imagen es ambigua. No deducir medidas, precios, stock ni correspondencias de prefijos no documentadas.
4. Contrastar las categorías de referencia con el PDF. Si hay diferencias, actualizar los registros de categorías antes de importar; el importador no crea categorías desconocidas automáticamente.
5. Preparar las fotografías en `app/static/img/products/` y completar el CSV UTF-8.
6. Ejecutar el comando con `--reviewed` únicamente después de revisar el PDF y verificar las filas del CSV.

```bash
.venv/bin/python -m flask --app run import-catalog data/catalog_seed.csv --reviewed
```

La aplicación no reconoce productos automáticamente. `scripts/extract_catalog.py` reproduce los recortes y el CSV de este PDF previamente revisado; exige su SHA-256 original y utiliza Poppler e ImageMagick. Ejecutar `.venv/bin/python scripts/extract_catalog.py` desde la raíz para reproducirlos. El manifiesto registra página, casilla, código impreso, coordenadas de recorte y hash de cada imagen. La portada respalda personalización; la publicación web sigue la solicitud de importar productos válidos. No se infieren precios, medidas ni disponibilidad. Un PDF diferente exige nueva revisión visual antes de adaptar el script.

Columnas CSV, en este orden:

```text
code,name,category,image,description,size_notes,allows_customization,is_active
```

- `code`: obligatorio, exacto, formato `FY.PREFIJO.001`; conserva `Ñ` y ceros iniciales. Los códigos `000` se rechazan siempre.
- `category`: nombre exacto de una categoría existente en SQLite.
- `name`, `description`, `size_notes`: pueden quedar vacíos si no se conocen. El nombre vacío genera advertencia y la tienda muestra el código.
- `image`: ruta relativa a `app/static/img/products/`, en JPG, JPEG, PNG o WebP. Si falta el archivo, se advierte y se utiliza el marcador neutro. Rutas fuera de esa carpeta se rechazan.
- `allows_customization`, `is_active`: `1` o `0`, obligatorios. No se infieren valores. `is_active` significa publicación en la web, **no existencia de stock ni disponibilidad comercial**. Si la personalización está pendiente de confirmar, mantener `0` y permitir la consulta por WhatsApp.
- CSV con comas, comillas o saltos en campos debe respetar el formato CSV estándar.

La importación informa creados, actualizados, omitidos, errores y advertencias. Rechaza todas las apariciones de un código repetido dentro del archivo. Los registros válidos se guardan aunque otras filas sean inválidas; con errores, el comando termina con código de salida 1. Corregir y volver a importar es seguro: actualiza por código sin duplicar productos.

El CSV controla la imagen principal (`sort_order=0`); las imágenes adicionales se conservan. No modifica `is_featured` ni elimina productos ausentes del CSV. Todavía no hay interfaz para gestionar destacados o imágenes adicionales.

## Estructura

```text
app/
  __init__.py                 Application factory, CSRF, cabeceras y comandos
  extensions.py              SQLAlchemy
  models/                    Category, Product, ProductImage
  main/                      Inicio, contacto, favoritos
  catalog/                   Catálogo, categorías, búsqueda, detalle, consulta de códigos
  orders/                    Carrito y vista previa de cotización
  services/                  Importación CSV, búsqueda Unicode, WhatsApp
  templates/                 Páginas Jinja2 y componentes compartidos
  static/
    css/                     Diseño y adaptación responsive
    js/                      Interacciones, favoritos y carrito
    img/
      placeholder.svg        Marcador neutro, sin apariencia de producto inventada
      products/              Fotografías verificadas
      branding/              Reservado para recursos de marca
      banners/               Reservado para recursos de portada
instance/
  tienda.db                  SQLite local, excluido de Git
  .session_key               Clave de desarrollo generada con permisos restringidos
  .gitkeep
data/catalog_seed.csv       173 productos verificados en el PDF
docs/                       PDF, manifiesto, imágenes de revisión y resultados de pruebas
deploy/                     Ejemplos de Nginx y systemd
tests/                      unittest de Python y pruebas de almacenamiento JS
config.py                   Configuración por entorno (get_config)
.env.example                Plantilla sin secretos con todas las variables
wsgi.py                     Entrada WSGI para Gunicorn
run.py                      Servidor de desarrollo
requirements.txt
requirements-postgres.txt   Opcional: solo para PostgreSQL
.gitignore
README.md
```

## Datos y responsabilidades

Tres tablas: `categories`, `products`, `product_images`. Relaciones categoría → productos → imágenes, identificadores numéricos, claves foráneas habilitadas, códigos y slugs únicos. Sin precios, pagos, usuarios, pedidos persistidos ni stock. Las categorías se consultan desde SQLite, no están incrustadas en HTML.

Flask valida los datos y genera las páginas. La búsqueda normaliza mayúsculas y acentos, preservando la diferencia entre `Ñ` y `N`; trata `%` y `_` como caracteres literales. JavaScript gestiona la selección y la interfaz con APIs del navegador, sin framework ni compilación.

## Carrito, favoritos y privacidad

Claves de localStorage:

- `yoli.favorites.v1`: lista de códigos.
- `yoli.cart.v1`: lista de objetos `product_code`, `quantity`, `requested_size`, `personalization`.

Las solicitudes de clientes autenticados limpian únicamente las cantidades y variantes enviadas cuando el servidor confirma la creación. Los errores conservan el carrito y los favoritos. El botón queda bloqueado durante el envío; una clave de reintento en `sessionStorage` (`yoli.request.v1`) permite recuperar la misma solicitud si se pierde la respuesta. El servidor registra la clave y la huella del contenido en la auditoría de creación, dentro de la misma transacción, sin cambiar el formato del carrito ni el esquema de la base de datos.

Selecciones con igual código, tamaño y personalización suman cantidades. Con personalizaciones o tamaños distintos permanecen separadas. Límites de interfaz: 100 favoritos, 50 líneas por solicitud, 1–99 unidades por línea. La selección persiste solo en ese navegador; se puede perder al borrar sus datos. Los cambios se sincronizan entre pestañas del mismo origen.

No se guarda nombre, ciudad ni entrega en localStorage o en la sesión Flask. La sesión solo contiene un token CSRF. La vista previa se devuelve con `Cache-Control: no-store`.

Antes de preparar una cotización, Flask vuelve a consultar los códigos y exige producto y categoría publicados, cantidades válidas y opciones permitidas. Los nombres de producto del navegador no se consideran confiables. Se escapan textos en HTML y JavaScript utiliza `textContent` para datos variables.

## WhatsApp

El cliente revisa el carrito, introduce nombre, ciudad y modalidad, y ve una vista previa generada por Flask. Luego abre cualquiera de los números de WhatsApp y pulsa enviar allí. La web no marca ventas ni afirma que el mensaje fue enviado. Las solicitudes extensas tienen copia de texto para evitar enlaces demasiado largos.

- 0969080116 → 593969080116
- 0986791895 → 593986791895
- figurasdefomixyoli@gmail.com
- Matriz San Gabriel; Sucursal Tulcán
- Envíos a todo Ecuador

No existe una asociación confirmada entre teléfonos y sucursales. No se publican direcciones exactas, horarios ni tarifas inventadas.

## Pruebas

```bash
.venv/bin/python -m unittest discover -s tests -v
node tests/test_storage.cjs
node --check app/static/js/app.js
node --check app/static/js/catalog.js
node --check app/static/js/favorites.js
node --check app/static/js/cart.js
```

Node se usa únicamente para pruebas opcionales del JavaScript; no es dependencia de ejecución de la tienda y no requiere paquetes npm. Python usa `unittest`, incluido en la biblioteca estándar. Las pruebas crean archivos temporales dentro de `instance/` y los eliminan al finalizar; nunca modifican `tienda.db`. `tests/test_production.py` cubre la configuración por entorno (incluye el rechazo de `SECRET_KEY` débil en producción), la cabecera de seguridad, `/health`, las páginas 403/404/429/500 y el control de hosts confiables.

## Panel administrativo

El blueprint `app/admin/` (prefijo `/admin`) ofrece autenticación y edición de
productos, categorías, destacados, orden, imágenes e importación con control de
errores, más la operación comercial (materiales, recetas, cálculos, clientes,
cotizaciones y facturas). Las migraciones de esquema se aplican con el
procedimiento verificado de la sección de producción; cuando haya una base
PostgreSQL con datos reales se introducirá Alembic.

Respaldar `instance/tienda.db` junto con las imágenes verificadas
(`backup-db`, ver [docs/production-backup.md](docs/production-backup.md)). La
clave se configura con `SECRET_KEY` (requerida y validada en staging/production);
la alternativa local se genera en `instance/.session_key`. No compartir esa clave
ni subirla a Git.

### Verificación del catálogo real y navegador

`python -m unittest discover -s tests -v` ejecuta también las comprobaciones de procedencia, códigos, imágenes, filtros, fichas, paginación, importación idempotente y cotización usando SQLite aislado. Usar el Python de `.venv`.

`node tests/test_storage.cjs` comprueba almacenamiento y límites del carrito. `node tests/browser_check.mjs` requiere Flask en 127.0.0.1:5000 y Chrome headless con DevTools en 127.0.0.1:9222 y perfil desechable: borra solo el localStorage de ese perfil. Guarda capturas y resultados en `docs/name-review/`, sin abrir WhatsApp ni enviar mensajes.

Producción con datos reales (panel administrativo)
------------------------------------------------

Materiales, recetas y calculadora requieren rol **admin**. El vendedor puede
cotizar con recetas activas, sin editar costos ni autorizar precios manuales.
Desde **Materiales**, registre las unidades configuradas y el costo real. Desde
**Calculadora**, seleccione el material guardado para vincularlo a la receta;
las filas ingresadas a mano mantienen sus propios costos. Una receta corresponde
a una variante y a una figura. Puede registrar tiempo en horas o minutos; los
indirectos son importes fijos por figura. Guarde el cálculo como receta y use
**Recetas** para buscar, duplicar, actualizar, activar/desactivar o cotizar.

Un nuevo cálculo de una receta vinculada usa el costo vigente del material.
Los cálculos guardados, cotizaciones y facturas conservan sus importes históricos.
Las recetas anteriores sin vínculo se conservan: el administrador debe sustituir
expresamente sus filas por materiales guardados si desea actualizar costos
mediante ese vínculo. No se asocian materiales por coincidencia de nombre.

Antes de usar esta versión en otra copia SQLite existente:

```bash
.venv/bin/python -m flask --app run upgrade-db
```

La migración respalda la base y añade `product_cost_recipes.is_active`. Para una
copia de seguridad completa en cualquier momento:

```bash
.venv/bin/python -m flask --app run backup-db
```

Las copias verificadas quedan en `instance/backups/`. Conserve también una copia
fuera del equipo; el respaldo SQLite cubre todos los datos comerciales, pero no
las imágenes, el PDF ni la clave de sesión. Para recuperar datos, detenga Flask,
verifique la copia con `PRAGMA integrity_check`, pruébela como una base separada
y conserve la base actual antes de sustituirla. No use `init-db` ni reimporte
el catálogo como procedimiento de recuperación.

Informe y evidencias de esta fase: [docs/production-review/report.md](docs/production-review/report.md).

## Preparación para despliegue (no publicado)

El código está listo para una futura puesta en producción sin que la tienda esté
desplegada todavía. Comprende:

- Configuración por entorno en `config.py` (`APP_ENV`, `SECRET_KEY` validada en
  staging/production, `DATABASE_URL`, cookies, hosts confiables, log).
- Servidor WSGI (`wsgi.py`) y Gunicorn en `requirements.txt`.
- Ajustes de seguridad: cookies seguras, `X-Content-Type-Options`,
  `Referrer-Policy`, `X-Frame-Options: DENY`, `Permissions-Policy`, CSP y HSTS
  condicional bajo HTTPS; `ProxyFix` detrás de Nginx; páginas 403/404/429/413/500
  sin volcar excepciones; `/health` para sondeos de carga.
- Portabilidad de base: numeración atómica (`documents.next_number` — upsert),
  serialización de escritura (`BEGIN IMMEDIATE`) y búsqueda (`search_normalize`)
  detectan el dialecto; `requirements-postgres.txt` instala el driver solo cuando
  `DATABASE_URL` use PostgreSQL. Alembic se documenta para esa fase futura.
- Operación: `backup-db` y `upgrade-db` verificados (SQLite), respaldo externo y
  guías en `docs/deployment.md` y `docs/production-backup.md`; ejemplos de Nginx
  y systemd en `deploy/` con placeholders de dominio.
- Pruebas nuevas en `tests/test_production.py`; todas las suites siguen en verde.

Sin cambios sobre `instance/tienda.db` (intacta y fuera de los commits): no se
migró a PostgreSQL, no se reimportó el catálogo y no se instaló nada en ningún
servidor.
