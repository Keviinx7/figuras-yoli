# Preparación del panel para datos reales de producción

Trabajo sobre el proyecto existente, sin commit ni push. Se conserva Flask/Jinja/SQLAlchemy, el catálogo oficial y todos los datos locales previos.

**A. Qué encontré**

Antes de editar: `git status --short` mostraba únicamente ` M instance/tienda.db`. `git log --oneline -6` devolvió los cinco commits existentes, encabezados por `985f997 fix: aplica redondeo comercial consistente`.

La aplicación usa una fábrica Flask, blueprints por módulo, plantillas Jinja, SQLAlchemy y SQLite. El dinero se almacena como texto Decimal mediante `ExactDecimal`; los documentos usan snapshots y redondeo HALF_UP. La suite inicial pasó 100 pruebas Python y 13 JavaScript.

Las recetas tenían `material_id`, pero al guardarlas no se establecía ese vínculo: solo copiaban nombre, unidad y costo. El vendedor podía consultar y modificar costos desde la calculadora. Materiales tenía todos los formularios abiertos, sin búsqueda ni orden por costo. Las recetas estaban al pie de la calculadora. El historial mostraba UTC. En móvil, algunas tablas comprimían palabras y acciones letra por letra.

**B. Qué cambié**

Vínculos explícitos a materiales, recálculo con costos vigentes, precios comerciales visibles antes de cotizar, separación de permisos, gestión independiente de recetas, paginación de 25 registros, unidades consistentes, fechas locales y ajustes del panel. Se añadió únicamente `product_cost_recipes.is_active BOOLEAN NOT NULL DEFAULT 1` al esquema existente, mediante migración aditiva y respaldo previo. No se crearon datos de producción.

La comparación posterior confirmó que todos los registros y columnas anteriores de las 19 tablas siguen idénticos. Permanecen 173 productos, 17 categorías, 173 imágenes, 1 material, 1 receta, 4 cálculos, 1 cliente, 6 cotizaciones, 2 facturas y el historial previo. `integrity_check = ok`; `foreign_key_check = []`. Evidencia: [data-verification.json](data-verification.json).

Respaldo anterior a la migración: `instance/backups/tienda-upgrade-20260913T195943825518Z.db`. El comando `flask backup-db` permite copias completas verificadas, sin reimportación. README incluye uso y recuperación prudente; una copia en el mismo disco no protege frente a pérdida del equipo.

**C. Archivos modificados**

- `README.md`: flujo de producción, actualización y respaldos.
- `app/__init__.py`, `app/services/dates.py` (nuevo): filtro horario.
- `app/admin/routes.py`: normalización y protección de unidades usadas.
- `app/costs/routes.py`, `app/services/production.py` (nuevo): material vigente, recetas, permisos, búsquedas y paginación.
- `app/models/commercial.py`, `app/services/commercial.py`: estado de receta, migración y backup.
- `app/quotes/routes.py`, `app/services/documents.py`: selección de variante, precio sugerido, auditoría manual y vencimiento según fecha local.
- `app/static/js/admin.js`, `app/static/css/admin.css`: interacción y adaptación visual.
- Plantillas `app/templates/admin/`: `base.html`, `costs.html`, `materials.html`, `recipes.html` (nuevo), `quote_form.html`, `products.html`, `dashboard.html`, `customer.html`, `documents.html`, `document_body.html`, `macros.html`.
- `tests/test_commercial.py`, `tests/test_admin_js.cjs`, `tests/browser_commercial.mjs`, `tests/browser_commercial_server.py`: regresiones y navegador aislado configurable.
- `instance/tienda.db`: modificación previa del usuario más columna aditiva, con los valores previos preservados.
- `docs/production-review/`: informe, resultados, estado Git y capturas.

**D. Materiales y unidades**

Creación y edición desplegable; búsqueda sin distinguir mayúsculas; orden alfabético o numérico por costo; paginación; activo/inactivo. Se rechazan nombres duplicados por diferencias solo de mayúsculas o espacios, costos negativos y unidades fuera de configuración. El costo conserva Decimal completo.

La configuración normaliza mayúsculas y plurales comunes, como Hoja/Hojas/hojas → hoja y mililitro → ml. No se añadieron unidades al negocio. Se impide retirar unidades usadas por materiales y cambiar la unidad de un material vinculado a recetas: no hay conversiones implícitas de cantidades. Los materiales inactivos quedan fuera del selector de nuevas filas, pero siguen disponibles en recetas existentes y documentos históricos.

**E. Calculadora**

Se conserva el servicio Decimal original y su precisión de 40 dígitos. La interfaz explica materiales + mano de obra + indirectos = costo real, y costo real + ganancia = precio antes de IVA. Horas y minutos ya existían; ahora se explica expresamente 0.75 horas = 45 minutos. No se fijó costo por hora.

Los indirectos son importes fijos por una figura. Para un gasto por lote, se indica dividir por las figuras del lote antes de introducirlo. No se crearon conceptos ni costos. Se mantienen las fórmulas de markup `costo × (1 + porcentaje/100)` y margen `costo ÷ (1 − porcentaje/100)`, con margen menor al 100% y sin valores negativos.

El bloque comercial muestra precio unitario redondeado, subtotal, IVA y total sugerido. Se diferencia del desglose interno anterior al redondeo. La prueba confirma **0.975 → 0.98 × 10 = 9.80; IVA 15% = 1.47; total = 11.27**, igual que cotización y factura. Un descuento incompatible con el subtotal comercial se rechaza antes de guardar el cálculo.

**F. Recetas**

Página independiente con código/producto, variante/tamaño, notas, fecha de actualización, costo vigente y precio sugerido antes de IVA. Búsqueda por código, producto, nombre y tamaño; orden por actualización; 25 resultados por página. Crear desde cálculo, editar/recalcular, duplicar variante, activar/desactivar y abrir cotización con producto/variante seleccionados.

Cada receta corresponde a una figura de una variante. Al elegir un material guardado, se guarda su identificador y el servidor toma el costo vigente; nombre, unidad y costo aparecen de solo lectura en esa fila. La cantidad sigue siendo editable y decimal. Para reemplazar un componente se quita la fila y se elige otro material. Para cambiar el costo maestro se usa Materiales.

Las recetas anteriores sin vínculo se mantienen como filas manuales. No se asocian automáticamente por nombre. El administrador puede reemplazarlas expresamente por materiales guardados. Una receta inactiva no se admite como fuente directa de una nueva cotización; los documentos anteriores siguen disponibles.

**G. Qué ocurre cuando cambia el costo de un material**

| Registro / acción | Comportamiento |
|---|---|
| Material | Guarda el nuevo costo Decimal autorizado por admin. |
| Receta vinculada | Al abrirla o calcularla, resuelve el costo vigente del material, conservando cantidad y unidad. |
| Receta con fila manual/antigua sin vínculo | Conserva su costo ingresado hasta edición explícita. |
| Cálculo nuevo | Toma los costos vigentes si proviene de receta/material vinculado. |
| Cálculo ya guardado | Conserva la entrada y resultado originales. Usarlo de nuevo usa esa copia fija. |
| Cotización nueva desde receta | Calcula con el costo vigente al guardar y crea su propio snapshot. |
| Cotización nueva desde cálculo guardado | Usa el costo y precio de ese cálculo fijo; para actualizar, generar otro cálculo. |
| Cotización histórica | Leer, imprimir o cambiar estado no recalcula sus importes. Solo un borrador puede editarse expresamente. |
| Factura histórica | Conserva exactamente los importes transferidos de la cotización, sin consultar costos actuales. |

Las regresiones cambian un costo TEST de 0.60 a 0.75, con cantidad 0.5, comprueban el costo nuevo 0.375, y contrastan snapshots/importes de la cotización y factura originales después del cambio y de desactivar el material.

**H. Permisos y precio manual**

Admin: materiales, recetas, calculadora, costos internos, precios manuales, recargos y descuentos. Vendedor: clientes, cotizaciones y operación comercial permitida; puede seleccionar recetas activas, pero recibe 403 ante lectura o escritura directa de la calculadora, materiales o gestión de recetas. Se retiraron esos accesos de su navegación. Se conservan las comprobaciones de propiedad sobre cálculos guardados y las restricciones comerciales existentes.

El selector de recetas muestra producto, variante y precio sugerido antes de IVA; el JavaScript filtra las fuentes según producto y el servidor valida la correspondencia. El precio manual sigue disponible para admin. Dejarlo vacío usa el sugerido. Si lo reemplaza, se conservan `manual_price` y `authorized_by` en el snapshot y se registra un evento `manual_price` en auditoría.

La tienda pública y los documentos imprimibles no exponen costos, mano de obra ni porcentajes de ganancia. Las pruebas incluyen un material TEST con datos internos distinguibles y comprueban su ausencia en páginas públicas.

**I. Zona horaria**

Se mantiene UTC en almacenamiento. `utcnow()` ya producía UTC; los valores SQLite sin tzinfo se interpretan conforme a esa convención existente. Los valores con zona conservan su offset y se convierten con `ZoneInfo('America/Guayaquil')`; no se restan cinco horas a ciegas. Historial, fechas de documentos y pagos se muestran con fecha, hora y zona explícitas. Las fechas de vencimiento siguen siendo fechas civiles, sin desplazarlas; su vigencia se compara con el día actual en Ecuador. Pruebas cubren cruce de medianoche, UTC consciente, UTC almacenado sin tzinfo y un valor ya local.

**J. Resultados de pruebas**

- Inicial: 100 Python, 9 JS de almacenamiento y 4 JS administrativos, todos correctos.
- Final Python: **113/113**, `unittest discover -s tests -v`, **45.068 s**, OK.
- Final JavaScript: **9/9 almacenamiento + 6/6 administrativos = 15/15**.
- Chrome comercial: **69 checks**, incluidos 48 checks de ancho (12 pantallas × 4 tamaños), sin excepciones JavaScript.
- Chrome público: **89 checks**, sin envío externo.
- `git diff --check`: limpio.

Se conservaron los 100 escenarios Python previos. Tres escenarios adaptan el permiso anterior de vendedor para respetar la prohibición solicitada sobre costos; no se eliminaron pruebas. Los avisos `ResourceWarning` de conexiones SQLite sin cerrar ya aparecían en la suite inicial y no provocan fallos.

Evidencias: [python-tests.txt](python-tests.txt), [js-tests.txt](js-tests.txt), [admin-browser/results.json](admin-browser/results.json), [public-browser/browser-results.json](public-browser/browser-results.json).

**K. Revisión visual real**

Chrome a 1440, 768, 390 y 320 px: dashboard, clientes, historial de cliente, materiales, calculadora con receta, recetas, formulario/listado de cotizaciones, listado/detalle de facturas, usuarios y configuración. Se generaron capturas y se inspeccionaron visualmente formularios, tablas, resultados y navegación en anchos representativos, incluyendo tablet y 320 px.

Se ajustaron rejillas estrechas de tablet, controles de materiales vinculados, búsqueda adaptable, métricas a 320 px, fieldsets y separación de botones. La inspección detectó la acción Editar dividida letra por letra en Usuarios: las tablas ahora mantienen ancho legible dentro de un contenedor desplazable, con indicación visible y foco de teclado. No hay overflow de la página; las tablas anchas conservan desplazamiento interno. Se mantuvieron colores, tipografía e identidad del panel y la impresión.

Capturas representativas: [Materiales 320](admin-browser/materials-320.png), [Calculadora 768](admin-browser/costs-768.png), [Recetas 1440](admin-browser/recipes-1440.png), [Cotización 390](admin-browser/quote-form-390.png), [Usuarios 390](admin-browser/users-390.png), [Configuración 320](admin-browser/configuration-320.png), [Factura 320](admin-browser/invoice-320.png).

Los escenarios nuevos de navegador usan nombres TEST y una copia aislada de SQLite en `instance/commercial-check/`, con usuarios temporales. No modifican el catálogo oficial ni agregan datos TEST a `instance/tienda.db`. Un intento de repetición encontró el servidor de pruebas detenido y terminó por timeout de navegación; tras reiniciarlo se ejecutaron nuevamente los checks. No hubo envío real de WhatsApp, pagos en línea ni implementación SRI.

**L. Pendientes que requieren datos del negocio**

Cargar o validar materiales reales y sus unidades/costos; tiempo por variante y tarifa por hora; indirectos por figura; cantidades de componentes; tamaños y personalizaciones reales; método y porcentaje de ganancia; notas de fabricación. Revisar y vincular expresamente las filas de recetas antiguas cuando corresponda. Confirmar moneda/IVA propios antes de emitir nuevos documentos. FY.VAR.019 sigue en revisión humana, sin cambios de catálogo.

**M. Estado Git final**

Sin commit, push, archivos preparados en staging ni cambios del catálogo. La base ya estaba modificada al inicio y ahora incorpora además la columna aditiva. El listado exacto se guarda en [git-status.txt](git-status.txt).
