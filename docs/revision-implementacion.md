# Informe de importación: Yoli Figuras de Fomix

Este informe conserva el resultado histórico de la importación. La fase posterior de nombres y revisión visual se documenta en [name-review/report.md](name-review/report.md): 149 nombres añadidos, uno corregido y un producto pendiente.

## Resultado

Se continuó la implementación existente, sin reconstruirla. Se revisaron visualmente y mediante extracción de texto las **33 páginas** del PDF auténtico. Resultado: **173 productos con código válido**, más **9 diseños reales de carátulas sin código**, pendientes de identificación comercial. SQLite contiene **17 categorías, 173 productos activos y 173 imágenes asociadas**.

CSV completado en `data/catalog_seed.csv`. Se extrajeron **182 imágenes PNG** a `app/static/img/products/`: 173 vinculadas a productos y 9 carátulas identificadas únicamente por página/casilla. **Imágenes pendientes de extracción: 0**. Las carátulas no se importaron ni recibieron códigos inventados.

## Criterios de revisión

- Se descartaron **77 apariciones .000**, no 77 productos distintos.
- Las páginas 31–33 son plantillas con logotipos. Además de los siete .000 de la página 33, se excluyeron **20 casillas con códigos no nulos**: nueve FY.AN.001, nueve FY.TOP.001, FY.CAR.001 y FY.CAR.002. No sustituyen las fotografías auténticas de esos productos.
- Se conservaron prefijos, Ñ y ceros iniciales. Se eliminaron únicamente espacios de maquetación: `FY.ÑA. 012` → `FY.ÑA.012`. El texto original permanece en el manifiesto.
- **FY.ÑA.011 no aparece** en el PDF. La secuencia pasa de FY.ÑA.010 a FY.ÑA.012. No se completó artificialmente.
- Se transcribieron 23 nombres explícitos. Los otros 150 registros conservan nombre vacío y muestran su código; no se asignaron nombres comerciales a partir de interpretaciones de las fotos.
- No se inventaron precios, medidas ni descripciones. `size_notes` y `description` permanecen vacíos. Los rótulos y cantidades impresos siguen visibles en los recortes.
- La personalización se habilitó según la declaración general de la portada: diseño, colores, tamaño, nombres, frases y detalles. La publicación responde a la solicitud del usuario; no afirma stock ni disponibilidad.

## Categorías

| Categoría | Productos importados | Diseños sin código |
|---|---:|---:|
| Animales | 38 | 0 |
| Capacidades diferentes | 1 | 0 |
| Carteles | 5 | 0 |
| Cuerpo humano y células | 13 | 0 |
| Etnias y regiones | 4 | 0 |
| Instrumentos musicales | 7 | 0 |
| Navideños | 6 | 0 |
| Niñas | 17 | 0 |
| Niños | 11 | 0 |
| Oficios y profesiones | 9 | 0 |
| Paquetes | 6 | 0 |
| Peces | 6 | 0 |
| Personajes | 16 | 0 |
| Religiosos | 11 | 0 |
| Toppers | 4 | 0 |
| Varios | 19 | 0 |
| Carátulas | 0 | 9 |
| **Total** | **173** | **9** |

Los títulos «Cuerpo humano» y «Cuerpo humano y células» se agruparon en la categoría existente «Cuerpo humano y células»; «Etnias/Regiones» corresponde a «Etnias y regiones». Rectángulos, Cuadrado y Rectángulo horizontal son encabezados de las plantillas finales, no categorías comerciales adicionales verificadas.

## Páginas analizadas

| Página | Productos con código | Diseños sin código | .000 excluidos | Logotipos con código no nulo excluidos |
|---|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 |
| 2 | 9 | 0 | 0 | 0 |
| 3 | 9 | 0 | 0 | 0 |
| 4 | 9 | 0 | 0 | 0 |
| 5 | 9 | 0 | 0 | 0 |
| 6 | 2 | 0 | 7 | 0 |
| 7 | 1 | 0 | 8 | 0 |
| 8 | 5 | 0 | 4 | 0 |
| 9 | 9 | 0 | 0 | 0 |
| 10 | 4 | 0 | 5 | 0 |
| 11 | 4 | 0 | 5 | 0 |
| 12 | 7 | 0 | 2 | 0 |
| 13 | 6 | 0 | 3 | 0 |
| 14 | 9 | 0 | 0 | 0 |
| 15 | 8 | 0 | 1 | 0 |
| 16 | 9 | 0 | 0 | 0 |
| 17 | 2 | 0 | 7 | 0 |
| 18 | 9 | 0 | 0 | 0 |
| 19 | 6 | 0 | 3 | 0 |
| 20 | 6 | 0 | 3 | 0 |
| 21 | 9 | 0 | 0 | 0 |
| 22 | 7 | 0 | 2 | 0 |
| 23 | 9 | 0 | 0 | 0 |
| 24 | 2 | 0 | 7 | 0 |
| 25 | 4 | 0 | 5 | 0 |
| 26 | 9 | 0 | 0 | 0 |
| 27 | 9 | 0 | 0 | 0 |
| 28 | 1 | 0 | 8 | 0 |
| 29 | 0 | 9 | 0 | 0 |
| 30 | 0 | 0 | 0 | 0 |
| 31 | 0 | 0 | 0 | 9 |
| 32 | 0 | 0 | 0 | 9 |
| 33 | 0 | 0 | 7 | 2 |

Página 1: portada, personalización y contactos. Página 29: nueve carátulas sin código. Página 30: cierre y contactos. Páginas 31–33: plantillas, excluidas.

## Evidencia reproducible

- `catalog-audit/manifest.json`: inventario completo por página y casilla, códigos originales, decisiones de exclusión, coordenadas de recorte y SHA-256 de cada imagen.
- `catalog-audit/text.txt` y `bbox.html`: extracción textual del PDF.
- `catalog-audit/page-01.jpg` a `page-33.jpg` y `sheet-1.jpg` a `sheet-6.jpg`: evidencia de la revisión visual de todas las páginas.
- `catalog-audit/source-02.png` a `source-29.png`: renders de origen para los recortes; no se generaron imágenes con IA ni se retocaron figuras.
- `scripts/extract_catalog.py`: reproducción de extracción y CSV, restringida mediante hash al PDF revisado. Requiere Poppler e ImageMagick.
- `catalog-audit/import.log`: primera importación, 173 creados, 0 actualizados, 0 omitidos, 0 errores. Las 150 advertencias son nombres no transcritos, sin imágenes faltantes.

SHA-256 del PDF: `52d58526c7c3ae074abe0cb6a8fe9656da0780e7b6c3cdaafbb52b2a1c7766bc`.

## Pruebas y Flask

- **40 pruebas Python aprobadas**: las 34 existentes y 6 integraciones nuevas del catálogo revisado.
- Las integraciones comprueban hash del PDF y las 182 imágenes, coincidencia de CSV y evidencia, exclusiones, Ñ, las 173 búsquedas por código, 173 fichas, 173 rutas de imagen, 17 filtros de categoría, 15 páginas del catálogo y reimportación idempotente.
- Cotización validada con productos reales de Niñas y Niños: los enlaces de ambos números conservan los códigos con Ñ y los datos solicitados, sin precios ficticios.
- **9 pruebas JavaScript aprobadas**, incluyendo el nuevo caso de datos de personalización inválidos. Sintaxis verificada en los cuatro scripts de la aplicación y el script de navegador.
- **18 verificaciones aprobadas en Chrome headless real**, con Flask: fotos, búsqueda, filtro, favoritos, almacenamiento persistente, cantidades, personalizaciones distintas, eliminación, cotización y enlaces WhatsApp. Sin excepciones JavaScript no capturadas.
- Capturas revisadas de catálogo en escritorio (1440 px) y móvil (390 px), detalle móvil y carrito móvil. Sin desbordamiento horizontal en los recorridos verificados. También se guardaron carrito y cotización de escritorio.
- Flask arrancó sin debug en `http://127.0.0.1:5000`. El catálogo respondió **HTTP 200** mediante una petición real; el recorrido completo del navegador utilizó ese servidor.
- No se enviaron mensajes a WhatsApp. Se comprobaron previsualización y enlaces de los dos números: 0969080116 y 0986791895.

Comandos: `.venv/bin/python -m unittest discover -s tests -v`; `node tests/test_storage.cjs`; `node --check` para los scripts; `node tests/browser_check.mjs`. Registros: `catalog-audit/python-tests.log`, `js-tests.log`, `browser-results.json` y capturas PNG.

## Errores corregidos

1. `app/static/js/app.js`: `addCart` podía guardar tamaño/personalización demasiado largos, notificar éxito y perder la línea al volver a leerla; además fallaba con valores no textuales. Ahora valida tipo y límites antes de escribir. Se reprodujo el fallo con una prueba que falló antes del cambio y pasó después.
2. Se resolvió el estado incompleto del catálogo: CSV vacío y SQLite sin productos, mediante extracción revisada e importación.
3. Se corrigieron README e informe anterior, que todavía afirmaban que el PDF no existía.
4. Durante la preparación de las pruebas se ajustó la espera de imágenes lazy-loading en Chrome y la selección de enlaces de cotización para distinguirlos de los contactos del pie de página; eran problemas de las pruebas, no fallos del producto.

## Antigravity

Se solicitó una revisión de solo lectura mediante `codex-agy-bridge.agy_ask`, con ámbito y prohibición explícita de modificar archivos. Resultado exacto: `agy timed out after 60.0s`. No devolvió hallazgos ni aprobación. No se atribuye la revisión local a Antigravity.

## Problemas pendientes y límites

- Nueve carátulas necesitan códigos comerciales auténticos antes de poder importarse. Sus imágenes ya están extraídas y trazadas.
- 150 fichas no tienen nombre transcrito; muestran su código. Precios, medidas concretas, disponibilidad y tiempos se confirman por WhatsApp porque el PDF no los especifica.
- No hay revisión independiente completada de Antigravity por timeout.
- No se comprobó envío dentro de la aplicación WhatsApp; no se enviaron mensajes.
- Git no reconoce este directorio como repositorio: `fatal: not a git repository`. No se reinicializó `.git`, no hay commits ni diff histórico verificable.
- Flask se verificó localmente como servidor de desarrollo. No se solicitó ni realizó despliegue público.

Todos los archivos del trabajo y las evidencias se guardaron dentro de `/home/kevin/Documentos/figuras-yoli`.
