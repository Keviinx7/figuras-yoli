# Revisión de nombres y presentación — 13 de septiembre de 2026

> Informe histórico de la revisión visual inicial. La [auditoría semántica posterior](catalog-name-audit.md) rectifica FY.CH.003 a **Endocrino**: el cambio a Sistema urinario documentado abajo fue incorrecto. Para nombres vigentes y validaciones nuevas, consultar esa auditoría.

Se trabajó sobre el CSV, SQLite y las imágenes ya existentes. No se volvió a extraer ni a importar el PDF completo. Se revisaron visualmente **173 productos** en las 15 hojas de contacto `sheet-01.jpg` a `sheet-15.jpg`, generadas a partir de sus recortes originales, y se ampliaron las imágenes ambiguas.

## Resultado

| Concepto | Cantidad |
|---|---:|
| Productos revisados | 173 |
| Nombres descriptivos añadidos | 149 |
| Nombres previos corregidos | 1 |
| Nombres previos conservados | 22 |
| Productos con nombre al finalizar | 172 |
| Productos pendientes de nombre | 1 |
| Productos modificados en SQLite | 150 |
| Productos conservados en SQLite | 173 |
| Diseños de carátulas sin código comercial | 9 |

Los nombres se basan en figuras y elementos visibles. Para personajes y etnias se prefirieron descripciones sin atribuir marcas, identidades o grupos no documentados. Ejemplos: Gato (FY.AN.001), Gallina (FY.AN.002), Corazón humano (FY.CH.010), Guitarra (FY.IM.002), Auto de carreras rojo (FY.PER.005), Niña con libro rojo (FY.ÑA.012). FY.IM.001 se denominó Bajo eléctrico por el instrumento de cuatro cuerdas visible.

La única corrección de un nombre previo fue **FY.CH.003: Endocrino → Sistema urinario**. El dibujo muestra riñones, uréteres y vejiga. Se conserva intacto el rótulo original dentro de la fotografía, sin retocar ni inventar partes del producto.

## Pendientes

- **FY.VAR.019** conserva nombre vacío y muestra su código. Se ve un corte anatómico parcial, pero la imagen no permite identificar con suficiente certeza el animal ni el sistema representado. La decisión está registrada en `review.json`.
- Las **nueve carátulas** permanecen identificadas por `uncoded-page-29-slot-01.png` a `uncoded-page-29-slot-09.png`, con referencias en el manifiesto de extracción. No se crearon códigos comerciales ni filas de producto para ellas.
- Los recortes conservan la calidad, orientación y contenido de la fuente: no se completaron con IA partes que no estuvieran disponibles. Precios, tamaños y disponibilidad no se modificaron.

## Actualización segura y trazabilidad

- `../../data/catalog_seed.csv`: se cambió exclusivamente la columna `name` en 150 filas; el resto de sus campos coincide exactamente con `before.csv`.
- `../../data/catalog_names.json`: registro de los nombres revisados, utilizado también por el extractor si se decide reproducir el catálogo en otra ocasión. El extractor **no se ejecutó** en esta fase.
- `../../scripts/update_catalog_names.py`: actualización de nombres por coincidencia exacta de códigos, sin crear filas. Valida que revisión, CSV y SQLite contengan los mismos códigos únicos y rechaza nombres modificados externamente.
- `tienda-before-names.db`: copia SQLite previa. La actualización usa una transacción y conserva IDs, códigos, slugs, categorías, publicación, personalización, destacados, descripciones, medidas, relaciones y rutas de imagen. Solo se actualizaron nombres, sus marcas de tiempo y textos alternativos que aún contenían el nombre anterior o el código.
- `database-update.json`: los 150 códigos modificados. `final-data-check.json`: comparación de campos con la copia previa, coincidencia de CSV/SQLite e integridad SQLite correcta, sin errores de claves foráneas.
- Los códigos con **Ñ** permanecen idénticos. No aparece FY.NA.012 ni se inventa FY.ÑA.011. No se eliminaron ni duplicaron productos.
- `review.json` y `changes.csv`: decisión, nombre previo, nombre final, estado, motivo y referencia de imagen para cada producto.

## Correcciones visuales

1. **Nombre y código separados:** tarjetas, favoritos y carrito presentan el nombre y `Código: FY.…`. El detalle conserva su código separado.
2. **Alineación de tarjetas:** el contenido usa una columna flexible para que nombres de distintas longitudes mantengan los botones alineados dentro de cada fila. En la captura inicial había diferencias de aproximadamente 20 px entre botones de la misma fila. Se añadieron límites de anchura y ajuste de palabras para nombres largos en tarjetas, detalle y carrito.
3. **FY.VAR.003:** el recorte previo cortaba el oso izquierdo. Se amplió únicamente ese recorte desde `../catalog-audit/source-26.png`, un render ya existente, sin volver a leer el PDF. Se conservaron imagen anterior, coordenadas y hashes en `FY.VAR.003-before.png` y `crop-correction.json`; el manifiesto de origen refleja el recorte corregido. Las otras 181 imágenes permanecen sin cambio.
4. **Inicio móvil:** se corrigió la anchura mínima de la columna y el tamaño adaptable del título. A 320 px, el contenedor ocultaba texto y enlaces aunque no hubiera barra horizontal; ahora el contenido queda visible.
5. **Inicio con catálogo publicado:** cuando no hay productos marcados como destacados, muestra ocho productos públicos en lugar de afirmar que el catálogo está en preparación. No se modificaron las banderas de destacados.
6. Se comprobaron imágenes con `object-fit: contain`, alturas por fila, códigos, categorías, nombres largos y textos. Se conservó la estructura general del diseño.

## Pruebas

- **43 pruebas Python aprobadas**: 40 existentes y 3 nuevas para nombres/búsqueda, actualización idempotente con rechazo de catálogo parcial, e inicio con productos públicos sin destacados.
- Las pruebas comprueban los 173 códigos, fichas e imágenes, búsqueda por todos los nombres disponibles, filtros de las 17 categorías, 15 páginas, Ñ, datos de cotización, fuentes de las 182 imágenes y exclusión de códigos inventados.
- **9 pruebas JavaScript aprobadas**; sintaxis válida en los cuatro scripts de aplicación y los scripts de pruebas.
- **89 comprobaciones Chrome aprobadas**, incluyendo las 18 previas. Se recorrieron las 15 páginas del catálogo a **1440, 390 y 320 px**, cotejando los 173 nombres/códigos, carga de imágenes, contención, alturas y botones alineados.
- Se revisaron inicio, categorías, filtros, tarjetas, detalle con nombre largo, favoritos y carrito en los tres anchos. Se verificó que el contenido del inicio no quedara oculto por recorte, además de comprobar ausencia de desbordamiento.
- Búsqueda real en Chrome por **Gato** y **FY.AN.001**: ambas localizan Gato con su código separado. Favoritos y carrito muestran nombres y conservan códigos como referencia estable.
- Cotización y ambos enlaces WhatsApp mantienen los códigos con Ñ; no se enviaron mensajes.
- Flask sin debug, disponible en `http://127.0.0.1:5000`; inicio comprobado por petición HTTP real con respuesta 200. HTML guardado en `flask-final.html`.

Comandos ejecutados: `.venv/bin/python -m unittest discover -s tests -v`, `node tests/test_storage.cjs`, `node --check` y `node tests/browser_check.mjs`. Resultados en `python-tests.log`, `js-tests.log` y `browser-results.json`. Las capturas `home-*`, `named-cards-*`, `categories-*`, `long-name-detail-*`, `named-favorites-*` y `named-cart-*` documentan la revisión visual. Se ajustó la espera de carga diferida de imágenes en el script de capturas para que los productos del inicio también quedaran incluidos.

## Inventario completo revisado

| Código | Nombre anterior | Nombre final | Resultado |
|---|---|---|---|
| FY.AN.001 | — | Gato | Nombre añadido |
| FY.AN.002 | — | Gallina | Nombre añadido |
| FY.AN.003 | — | Perro | Nombre añadido |
| FY.AN.004 | — | Caballo | Nombre añadido |
| FY.AN.005 | — | Pato | Nombre añadido |
| FY.AN.006 | — | Pato sentado | Nombre añadido |
| FY.AN.007 | — | Roedor | Nombre añadido |
| FY.AN.008 | — | Capibara con bebida | Nombre añadido |
| FY.AN.009 | — | Capibara con sandía | Nombre añadido |
| FY.AN.010 | — | Caracol | Nombre añadido |
| FY.AN.011 | — | Cocodrilo | Nombre añadido |
| FY.AN.012 | — | Elefante | Nombre añadido |
| FY.AN.013 | — | Oruga | Nombre añadido |
| FY.AN.014 | — | Ardilla | Nombre añadido |
| FY.AN.015 | — | Hormiga | Nombre añadido |
| FY.AN.016 | — | Jirafa | Nombre añadido |
| FY.AN.017 | — | León | Nombre añadido |
| FY.AN.018 | — | Mariposa | Nombre añadido |
| FY.AN.019 | — | Mariquita | Nombre añadido |
| FY.AN.020 | — | Mono | Nombre añadido |
| FY.AN.021 | — | Oso saludando | Nombre añadido |
| FY.AN.022 | — | Oso sentado | Nombre añadido |
| FY.AN.023 | — | Panda | Nombre añadido |
| FY.AN.024 | — | Pelícano | Nombre añadido |
| FY.AN.025 | — | Pollito | Nombre añadido |
| FY.AN.026 | — | Insecto verde | Nombre añadido |
| FY.AN.027 | — | Rana | Nombre añadido |
| FY.AN.028 | — | Serpiente | Nombre añadido |
| FY.AN.029 | — | Tortuga | Nombre añadido |
| FY.AN.030 | — | Tigre | Nombre añadido |
| FY.AN.031 | — | Cebra | Nombre añadido |
| FY.AN.032 | — | Vaca | Nombre añadido |
| FY.AN.033 | — | Loro | Nombre añadido |
| FY.AN.034 | — | Dinosaurio | Nombre añadido |
| FY.AN.035 | — | Unicornio | Nombre añadido |
| FY.AN.036 | — | Cerdo | Nombre añadido |
| FY.AN.037 | — | Paloma | Nombre añadido |
| FY.AN.038 | — | Conejo | Nombre añadido |
| FY.CD.001 | — | Niño con bastón y gafas | Nombre añadido |
| FY.CAR.001 | — | Bienvenidos al año lectivo | Nombre añadido |
| FY.CAR.002 | — | Banderín de bienvenida | Nombre añadido |
| FY.CAR.003 | — | Bienvenidos al nuevo año lectivo | Nombre añadido |
| FY.CAR.004 | — | Bienvenida con nombre de profesora | Nombre añadido |
| FY.CAR.005 | — | Banderín con nombre de profesora | Nombre añadido |
| FY.CH.001 | Digestivo | Digestivo | Nombre conservado |
| FY.CH.002 | Circulatorio | Circulatorio | Nombre conservado |
| FY.CH.003 | Endocrino | Sistema urinario | Error corregido |
| FY.CH.004 | Nervioso | Nervioso | Nombre conservado |
| FY.CH.005 | Respiratorio | Respiratorio | Nombre conservado |
| FY.CH.006 | Reproductor femenino | Reproductor femenino | Nombre conservado |
| FY.CH.007 | Reproductor masculino | Reproductor masculino | Nombre conservado |
| FY.CH.008 | — | Esqueleto humano | Nombre añadido |
| FY.CH.009 | — | Cerebro | Nombre añadido |
| FY.CH.010 | — | Corazón humano | Nombre añadido |
| FY.CH.011 | Célula animal | Célula animal | Nombre conservado |
| FY.CH.012 | Célula procariota | Célula procariota | Nombre conservado |
| FY.CH.013 | Célula vegetal | Célula vegetal | Nombre conservado |
| FY.ER.001 | — | Pareja con tocados de plumas | Nombre añadido |
| FY.ER.002 | — | Pareja con pañuelo y falda | Nombre añadido |
| FY.ER.003 | — | Pareja con sombreros | Nombre añadido |
| FY.ER.004 | — | Pareja con pañuelos amarillos | Nombre añadido |
| FY.IM.001 | — | Bajo eléctrico | Nombre añadido |
| FY.IM.002 | — | Guitarra | Nombre añadido |
| FY.IM.003 | — | Maracas | Nombre añadido |
| FY.IM.004 | — | Saxofón | Nombre añadido |
| FY.IM.005 | — | Tambor | Nombre añadido |
| FY.IM.006 | — | Violín | Nombre añadido |
| FY.IM.007 | — | Arpa | Nombre añadido |
| FY.NAV.001 | Melchor | Melchor | Nombre conservado |
| FY.NAV.002 | Baltazar | Baltazar | Nombre conservado |
| FY.NAV.003 | Gaspar | Gaspar | Nombre conservado |
| FY.NAV.004 | Bota navideña | Bota navideña | Nombre conservado |
| FY.NAV.005 | Reno navideño | Reno navideño | Nombre conservado |
| FY.NAV.006 | Muñeco de nieve | Muñeco de nieve | Nombre conservado |
| FY.ÑA.001 | — | Niña con lápiz y manzana | Nombre añadido |
| FY.ÑA.002 | — | Niña con libro azul | Nombre añadido |
| FY.ÑA.003 | — | Niña con lápiz y cuaderno | Nombre añadido |
| FY.ÑA.004 | — | Niña con vestido rosa | Nombre añadido |
| FY.ÑA.005 | — | Niña sentada leyendo | Nombre añadido |
| FY.ÑA.006 | — | Niña abrazando un lápiz | Nombre añadido |
| FY.ÑA.007 | — | Niña escribiendo | Nombre añadido |
| FY.ÑA.008 | — | Niña con delantal y manzana | Nombre añadido |
| FY.ÑA.009 | — | Niña con brazos abiertos | Nombre añadido |
| FY.ÑA.010 | — | Niña con libros | Nombre añadido |
| FY.ÑA.012 | — | Niña con libro rojo | Nombre añadido |
| FY.ÑA.013 | — | Niña con vestido y diadema | Nombre añadido |
| FY.ÑA.014 | — | Niña graduada | Nombre añadido |
| FY.ÑA.015 | — | Niña con cuaderno y lazo | Nombre añadido |
| FY.ÑA.016 | — | Niña leyendo un libro rojo | Nombre añadido |
| FY.ÑA.017 | — | Niña con cuerda de saltar | Nombre añadido |
| FY.ÑA.018 | — | Niña con overol y lápiz | Nombre añadido |
| FY.ÑO.001 | — | Niño con camiseta roja | Nombre añadido |
| FY.ÑO.002 | — | Niño con libro amarillo | Nombre añadido |
| FY.ÑO.003 | — | Niño con libro en la mano | Nombre añadido |
| FY.ÑO.004 | — | Niño en patineta | Nombre añadido |
| FY.ÑO.005 | — | Niño saludando | Nombre añadido |
| FY.ÑO.006 | — | Niño con overol azul | Nombre añadido |
| FY.ÑO.007 | — | Niño leyendo un libro verde | Nombre añadido |
| FY.ÑO.008 | — | Niño con mochila | Nombre añadido |
| FY.ÑO.009 | — | Niño graduado | Nombre añadido |
| FY.ÑO.010 | — | Niño con balón de fútbol | Nombre añadido |
| FY.ÑO.011 | — | Niño con lápiz | Nombre añadido |
| FY.OP.001 | — | Bombero | Nombre añadido |
| FY.OP.002 | — | Mecánico | Nombre añadido |
| FY.OP.003 | — | Policía con uniforme verde | Nombre añadido |
| FY.OP.004 | — | Enfermera con uniforme blanco | Nombre añadido |
| FY.OP.005 | — | Enfermera con uniforme azul | Nombre añadido |
| FY.OP.006 | Maestra | Maestra | Nombre conservado |
| FY.OP.007 | — | Policía con radio | Nombre añadido |
| FY.OP.008 | — | Cocinero | Nombre añadido |
| FY.OP.009 | — | Carpintero | Nombre añadido |
| FY.PAQ.001 | — | Paquete de útiles escolares | Nombre añadido |
| FY.PAQ.002 | — | Paquete de estrellas | Nombre añadido |
| FY.PAQ.003 | — | Paquete de los cinco sentidos | Nombre añadido |
| FY.PAQ.004 | — | Paquete de corazones | Nombre añadido |
| FY.PAQ.005 | — | Paquete de flores | Nombre añadido |
| FY.PAQ.006 | — | Paquete de huellas y huesos | Nombre añadido |
| FY.PE.001 | — | Pez azul y amarillo | Nombre añadido |
| FY.PE.002 | — | Pez verde y rosa | Nombre añadido |
| FY.PE.003 | — | Pez naranja y amarillo | Nombre añadido |
| FY.PE.004 | — | Pez amarillo y verde | Nombre añadido |
| FY.PE.005 | — | Pez azul | Nombre añadido |
| FY.PE.006 | — | Pez naranja con franjas blancas | Nombre añadido |
| FY.PER.001 | — | Oso con vaso | Nombre añadido |
| FY.PER.002 | — | Criatura azul de orejas grandes | Nombre añadido |
| FY.PER.003 | — | Erizo azul | Nombre añadido |
| FY.PER.004 | — | Superhéroe con telarañas | Nombre añadido |
| FY.PER.005 | — | Auto de carreras rojo | Nombre añadido |
| FY.PER.006 | — | Perro con libro | Nombre añadido |
| FY.PER.007 | — | Niño con traje rojo | Nombre añadido |
| FY.PER.008 | — | Gatita con flor | Nombre añadido |
| FY.PER.009 | — | Hada con vestido verde | Nombre añadido |
| FY.PER.010 | — | Perro bombero con cartel | Nombre añadido |
| FY.PER.011 | — | Perro policía con cartel | Nombre añadido |
| FY.PER.012 | — | Perro constructor con cartel | Nombre añadido |
| FY.PER.013 | — | Ratona con lazo rojo | Nombre añadido |
| FY.PER.014 | — | Cara de perro policía | Nombre añadido |
| FY.PER.015 | — | Cara de perro bombero | Nombre añadido |
| FY.PER.016 | — | Cara de perro constructor | Nombre añadido |
| FY.RE.001 | — | Sacerdote | Nombre añadido |
| FY.RE.002 | — | Ángel con alas rosas | Nombre añadido |
| FY.RE.003 | — | Ángel con alas azules | Nombre añadido |
| FY.RE.004 | — | Hombre con túnica | Nombre añadido |
| FY.RE.005 | — | Monja con rosario | Nombre añadido |
| FY.RE.006 | — | Virgen con manto verde | Nombre añadido |
| FY.RE.007 | Virgen de la Medalla Milagrosa | Virgen de la Medalla Milagrosa | Nombre conservado |
| FY.RE.008 | — | Virgen con manto azul | Nombre añadido |
| FY.RE.009 | — | Bebé en pesebre | Nombre añadido |
| FY.RE.010 | María | María | Nombre conservado |
| FY.RE.011 | José | José | Nombre conservado |
| FY.TOP.001 | — | Topper Felicitaciones | Nombre añadido |
| FY.TOP.002 | — | Topper Feliz Día Mamá | Nombre añadido |
| FY.TOP.003 | — | Topper Feliz Cumple | Nombre añadido |
| FY.TOP.004 | — | Topper Feliz Día | Nombre añadido |
| FY.VAR.001 | — | Mazo de juez | Nombre añadido |
| FY.VAR.002 | — | Frasco con pastillas | Nombre añadido |
| FY.VAR.003 | Identificativos | Identificativos | Nombre conservado |
| FY.VAR.004 | — | Volcán | Nombre añadido |
| FY.VAR.005 | — | Estetoscopio | Nombre añadido |
| FY.VAR.006 | — | Planeta Tierra en una mano | Nombre añadido |
| FY.VAR.007 | — | Esposas | Nombre añadido |
| FY.VAR.008 | Ciclo del agua | Ciclo del agua | Nombre conservado |
| FY.VAR.009 | — | Chaleco de policía | Nombre añadido |
| FY.VAR.010 | — | Botiquín | Nombre añadido |
| FY.VAR.011 | — | Bandera tricolor | Nombre añadido |
| FY.VAR.012 | — | Animal con cartel Feliz Día | Nombre añadido |
| FY.VAR.013 | — | Iglesia | Nombre añadido |
| FY.VAR.014 | — | Mapa del Ecuador | Nombre añadido |
| FY.VAR.015 | — | Casa | Nombre añadido |
| FY.VAR.016 | Identificativos | Identificativos | Nombre conservado |
| FY.VAR.017 | — | Cerdo con órganos internos | Nombre añadido |
| FY.VAR.018 | — | Anatomía interna del cerdo | Nombre añadido |
| FY.VAR.019 | — | Código (pendiente) | Pendiente |
