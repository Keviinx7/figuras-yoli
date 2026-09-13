# Auditoría de datos comerciales del catálogo oficial

Fuente única y prioritaria: [catalogo-productos.pdf](catalogo-productos.pdf), 33 páginas. Revisión realizada el 2026-09-13 antes de modificar la tienda para esta tarea.

SHA-256: `52d58526c7c3ae074abe0cb6a8fe9656da0780e7b6c3cdaafbb52b2a1c7766bc`.

**Este catálogo no contiene una lista de precios numéricos por producto; indica que los precios dependen del tamaño.**

Se revisaron visualmente las 33 páginas completas renderizadas desde el PDF y se contrastaron con su capa de texto (`pdftotext -layout`). La inspección visual incluye rótulos dentro de fotografías que la extracción de texto omite. El manifiesto previo se usa únicamente para localizar página, casilla y recorte; la autoridad comercial sigue siendo el PDF. Los renders y el texto de trabajo son temporales y no forman parte del commit.

## Criterios de clasificación

- «Nombre» transcribe el rótulo nominal explícito cuando existe. «No explícito» no borra los nombres descriptivos ya auditados de la tienda. Las frases decorativas, los nombres personalizados de ejemplo y las etiquetas dentro de un dibujo se distinguen en Observaciones; no se inventa un nombre de producto a partir de ellas.
- La categoría corresponde al encabezado de la página, con mayúsculas normalizadas. En la página 9 el PDF dice «Cuerpo humano»; la categoría vigente de la tienda «Cuerpo humano y células» agrupa las páginas 9 y 10 y permanece intacta. «Etnias/regiones» corresponde a la categoría vigente «Etnias y regiones».
- «No indicada» significa que no hay cantidad de paquete declarada. No se cuentan las figuras de una fotografía para deducir unidades vendidas. La página 19 imprime cinco cantidades; FY.PAQ.006 no tiene cantidad impresa.
- «No declarada» significa que no hay una medida explícita atribuida al producto. La elección libre de tamaño no define opciones S/M/L, centímetros, anchos ni altos. La base de corte visible en FY.PER.013 no es una especificación comercial.
- «No» en Precio explícito significa ausencia de importe numérico, no precio cero. «Los precios varían según el tamaño a su elección» (páginas 2–28 y 31–33) no se convierte en dinero. La página 29 dice «Los precios varían según el diseño a su elección»; tampoco contiene importes.
- **P1** en Observaciones remite al texto general de personalización de la portada, aplicable como oferta general: «Las personalizamos a tu gusto: diseño, colores, tamaño, agregamos nombres, frases, detalles y todo lo que necesites.!». No enumera variantes con precio o medidas fijas por código.
- Cada fila de producto enlaza su imagen existente y señala la casilla (lectura por filas, de izquierda a derecha). No se sustituyen imágenes ni se generan productos.
- Códigos, teléfonos, años escolares, el 95 del automóvil, numeración de la base de corte y cantidades X6/X24/X5/X20 no son precios. No aparecen costos de materiales, mano de obra, recetas ni tarifas administrativas en el PDF.

## Cobertura de las 33 páginas

| Página | Contenido revisado | Productos con código válido | Otras casillas / observaciones |
| --- | --- | ---: | --- |
| 1 | Portada y personalización general | 0 | Oferta general de personalización; sin productos codificados ni precios |
| 2 | Animales | 9 | Sin importes ni medidas declaradas |
| 3 | Animales | 9 | Sin importes ni medidas declaradas |
| 4 | Animales | 9 | Sin importes ni medidas declaradas |
| 5 | Animales | 9 | Sin importes ni medidas declaradas |
| 6 | Animales | 2 | 7 casillas .000 excluidas (logotipo) |
| 7 | Capacidades diferentes | 1 | 8 casillas .000 excluidas (logotipo) |
| 8 | Carteles | 5 | 4 casillas .000 excluidas (logotipo) |
| 9 | Cuerpo humano | 9 | Sin importes ni medidas declaradas |
| 10 | Cuerpo humano y células | 4 | 5 casillas .000 excluidas (logotipo) |
| 11 | Etnias/regiones | 4 | 5 casillas .000 excluidas (logotipo) |
| 12 | Instrumentos musicales | 7 | 2 casillas .000 excluidas (logotipo) |
| 13 | Navideños | 6 | 3 casillas .000 excluidas (logotipo) |
| 14 | Niñas | 9 | Sin importes ni medidas declaradas |
| 15 | Niñas | 8 | 1 casillas .000 excluidas (logotipo) |
| 16 | Niños | 9 | Sin importes ni medidas declaradas |
| 17 | Niños | 2 | 7 casillas .000 excluidas (logotipo) |
| 18 | Oficios y profesiones | 9 | Sin importes ni medidas declaradas |
| 19 | Paquetes | 6 | 3 casillas .000 excluidas (logotipo); Cinco cantidades de paquete explícitas; ningún importe |
| 20 | Peces | 6 | 3 casillas .000 excluidas (logotipo) |
| 21 | Personajes | 9 | Sin importes ni medidas declaradas |
| 22 | Personajes | 7 | 2 casillas .000 excluidas (logotipo) |
| 23 | Religiosos | 9 | Sin importes ni medidas declaradas |
| 24 | Religiosos | 2 | 7 casillas .000 excluidas (logotipo) |
| 25 | Toppers | 4 | 5 casillas .000 excluidas (logotipo) |
| 26 | Varios | 9 | Sin importes ni medidas declaradas |
| 27 | Varios | 9 | Sin importes ni medidas declaradas |
| 28 | Varios | 1 | 8 casillas .000 excluidas (logotipo) |
| 29 | Carátulas | 0 | 9 imágenes sin código; precio según diseño, sin importe |
| 30 | Cierre y contacto | 0 | Sin productos ni precios; teléfonos de contacto |
| 31 | Rectángulos (plantilla) | 0 | 9 casillas con códigos no cero y solo logotipo, excluidas |
| 32 | Cuadrado (plantilla) | 0 | 9 casillas con códigos no cero y solo logotipo, excluidas |
| 33 | Rectángulo horizontal (plantilla) | 0 | 7 casillas .000 excluidas (logotipo); 2 casillas con códigos no cero y solo logotipo, excluidas |

Total: **173 productos con código válido**, **9 carátulas sin código**, **77 casillas .000 excluidas** y **20 casillas de plantilla con códigos no cero excluidas**. Los códigos con Ñ se conservan exactamente. FY.ÑA.011 no se imprime: no se rellena ese salto.

## Productos auditados

| Página | Código | Nombre | Categoría | Cantidad/paquete | Medida explícita | Precio explícito | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | FY.AN.001 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.001.png); casilla 1. P1. |
| 2 | FY.AN.002 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.002.png); casilla 2. P1. |
| 2 | FY.AN.003 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.003.png); casilla 3. P1. |
| 2 | FY.AN.004 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.004.png); casilla 4. P1. |
| 2 | FY.AN.005 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.005.png); casilla 5. P1. |
| 2 | FY.AN.006 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.006.png); casilla 6. P1. |
| 2 | FY.AN.007 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.007.png); casilla 7. P1. |
| 2 | FY.AN.008 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.008.png); casilla 8. P1. |
| 2 | FY.AN.009 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.009.png); casilla 9. P1. |
| 3 | FY.AN.010 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.010.png); casilla 1. P1. |
| 3 | FY.AN.011 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.011.png); casilla 2. P1. |
| 3 | FY.AN.012 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.012.png); casilla 3. P1. |
| 3 | FY.AN.013 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.013.png); casilla 4. P1. |
| 3 | FY.AN.014 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.014.png); casilla 5. P1. |
| 3 | FY.AN.015 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.015.png); casilla 6. P1. |
| 3 | FY.AN.016 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.016.png); casilla 7. P1. |
| 3 | FY.AN.017 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.017.png); casilla 8. P1. |
| 3 | FY.AN.018 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.018.png); casilla 9. P1. |
| 4 | FY.AN.019 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.019.png); casilla 1. P1. |
| 4 | FY.AN.020 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.020.png); casilla 2. P1. |
| 4 | FY.AN.021 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.021.png); casilla 3. P1. |
| 4 | FY.AN.022 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.022.png); casilla 4. P1. |
| 4 | FY.AN.023 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.023.png); casilla 5. P1. |
| 4 | FY.AN.024 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.024.png); casilla 6. P1. |
| 4 | FY.AN.025 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.025.png); casilla 7. P1. |
| 4 | FY.AN.026 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.026.png); casilla 8. P1. |
| 4 | FY.AN.027 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.027.png); casilla 9. P1. |
| 5 | FY.AN.028 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.028.png); casilla 1. P1. |
| 5 | FY.AN.029 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.029.png); casilla 2. P1. |
| 5 | FY.AN.030 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.030.png); casilla 3. P1. |
| 5 | FY.AN.031 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.031.png); casilla 4. P1. |
| 5 | FY.AN.032 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.032.png); casilla 5. P1. |
| 5 | FY.AN.033 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.033.png); casilla 6. P1. |
| 5 | FY.AN.034 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.034.png); casilla 7. P1. |
| 5 | FY.AN.035 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.035.png); casilla 8. P1. |
| 5 | FY.AN.036 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.036.png); casilla 9. P1. |
| 6 | FY.AN.037 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.037.png); casilla 1. P1. |
| 6 | FY.AN.038 | No explícito | Animales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.AN.038.png); casilla 2. P1. |
| 7 | FY.CD.001 | No explícito | Capacidades diferentes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CD.001.png); casilla 1. P1. |
| 8 | FY.CAR.001 | No explícito | Carteles | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CAR.001.png); casilla 1. P1. Texto del diseño: «Bienvenidos año lectivo 2026–2027»; los años no son precios. |
| 8 | FY.CAR.002 | No explícito | Carteles | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CAR.002.png); casilla 2. P1. Texto del diseño: «Bienvenidos». |
| 8 | FY.CAR.003 | No explícito | Carteles | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CAR.003.png); casilla 3. P1. Texto del diseño: «Bienvenidos al nuevo año lectivo». |
| 8 | FY.CAR.004 | No explícito | Carteles | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CAR.004.png); casilla 4. P1. Rótulo «PERSONALIZADOS». Diseño con «Bienvenidos año lectivo 2026–2027» y «Profe Estefy»; ejemplo de nombre, no variante cerrada ni precio. |
| 8 | FY.CAR.005 | No explícito | Carteles | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CAR.005.png); casilla 5. P1. Rótulo «PERSONALIZADOS». Diseño con «Bienvenidos» y «Profe Raquel»; ejemplo de nombre, no variante cerrada. |
| 9 | FY.CH.001 | Digestivo | Cuerpo humano | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.001.png); casilla 1. P1. |
| 9 | FY.CH.002 | Circulatorio | Cuerpo humano | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.002.png); casilla 2. P1. |
| 9 | FY.CH.003 | Endocrino | Cuerpo humano | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.003.png); casilla 3. P1. Se transcribe «Endocrino» tal como está impreso, sin corregirlo por interpretación anatómica. |
| 9 | FY.CH.004 | Nervioso | Cuerpo humano | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.004.png); casilla 4. P1. |
| 9 | FY.CH.005 | Respiratorio | Cuerpo humano | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.005.png); casilla 5. P1. |
| 9 | FY.CH.006 | Reproductor femenino | Cuerpo humano | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.006.png); casilla 6. P1. |
| 9 | FY.CH.007 | Reproductor masculino | Cuerpo humano | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.007.png); casilla 7. P1. |
| 9 | FY.CH.008 | No explícito | Cuerpo humano | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.008.png); casilla 8. P1. |
| 9 | FY.CH.009 | No explícito | Cuerpo humano | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.009.png); casilla 9. P1. |
| 10 | FY.CH.010 | No explícito | Cuerpo humano y células | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.010.png); casilla 1. P1. |
| 10 | FY.CH.011 | Célula animal | Cuerpo humano y células | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.011.png); casilla 2. P1. |
| 10 | FY.CH.012 | Célula procariota | Cuerpo humano y células | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.012.png); casilla 3. P1. |
| 10 | FY.CH.013 | Célula vegetal | Cuerpo humano y células | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.CH.013.png); casilla 4. P1. |
| 11 | FY.ER.001 | No explícito | Etnias/regiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ER.001.png); casilla 1. P1. |
| 11 | FY.ER.002 | No explícito | Etnias/regiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ER.002.png); casilla 2. P1. |
| 11 | FY.ER.003 | No explícito | Etnias/regiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ER.003.png); casilla 3. P1. |
| 11 | FY.ER.004 | No explícito | Etnias/regiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ER.004.png); casilla 4. P1. |
| 12 | FY.IM.001 | No explícito | Instrumentos musicales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.IM.001.png); casilla 1. P1. |
| 12 | FY.IM.002 | No explícito | Instrumentos musicales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.IM.002.png); casilla 2. P1. |
| 12 | FY.IM.003 | No explícito | Instrumentos musicales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.IM.003.png); casilla 3. P1. |
| 12 | FY.IM.004 | No explícito | Instrumentos musicales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.IM.004.png); casilla 4. P1. |
| 12 | FY.IM.005 | No explícito | Instrumentos musicales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.IM.005.png); casilla 5. P1. |
| 12 | FY.IM.006 | No explícito | Instrumentos musicales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.IM.006.png); casilla 6. P1. |
| 12 | FY.IM.007 | No explícito | Instrumentos musicales | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.IM.007.png); casilla 7. P1. |
| 13 | FY.NAV.001 | Melchor | Navideños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.NAV.001.png); casilla 1. P1. |
| 13 | FY.NAV.002 | Baltazar | Navideños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.NAV.002.png); casilla 2. P1. |
| 13 | FY.NAV.003 | Gaspar | Navideños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.NAV.003.png); casilla 3. P1. |
| 13 | FY.NAV.004 | Bota navideña | Navideños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.NAV.004.png); casilla 4. P1. |
| 13 | FY.NAV.005 | Reno navideño | Navideños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.NAV.005.png); casilla 5. P1. |
| 13 | FY.NAV.006 | Muñeco de neive [sic] | Navideños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.NAV.006.png); casilla 6. P1. Se conserva aquí la grafía impresa «Muñeco de neive»; la tienda conserva su normalización anterior «Muñeco de nieve». |
| 14 | FY.ÑA.001 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.001.png); casilla 1. P1. |
| 14 | FY.ÑA.002 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.002.png); casilla 2. P1. |
| 14 | FY.ÑA.003 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.003.png); casilla 3. P1. |
| 14 | FY.ÑA.004 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.004.png); casilla 4. P1. |
| 14 | FY.ÑA.005 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.005.png); casilla 5. P1. |
| 14 | FY.ÑA.006 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.006.png); casilla 6. P1. |
| 14 | FY.ÑA.007 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.007.png); casilla 7. P1. |
| 14 | FY.ÑA.008 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.008.png); casilla 8. P1. |
| 14 | FY.ÑA.009 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.009.png); casilla 9. P1. |
| 15 | FY.ÑA.010 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.010.png); casilla 1. P1. |
| 15 | FY.ÑA.012 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.012.png); casilla 2. P1. |
| 15 | FY.ÑA.013 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.013.png); casilla 3. P1. |
| 15 | FY.ÑA.014 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.014.png); casilla 4. P1. La figura lleva un diploma; su texto no declara tamaño ni precio. |
| 15 | FY.ÑA.015 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.015.png); casilla 5. P1. |
| 15 | FY.ÑA.016 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.016.png); casilla 6. P1. |
| 15 | FY.ÑA.017 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.017.png); casilla 7. P1. |
| 15 | FY.ÑA.018 | No explícito | Niñas | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑA.018.png); casilla 8. P1. |
| 16 | FY.ÑO.001 | No explícito | Niños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑO.001.png); casilla 1. P1. |
| 16 | FY.ÑO.002 | No explícito | Niños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑO.002.png); casilla 2. P1. |
| 16 | FY.ÑO.003 | No explícito | Niños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑO.003.png); casilla 3. P1. |
| 16 | FY.ÑO.004 | No explícito | Niños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑO.004.png); casilla 4. P1. |
| 16 | FY.ÑO.005 | No explícito | Niños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑO.005.png); casilla 5. P1. |
| 16 | FY.ÑO.006 | No explícito | Niños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑO.006.png); casilla 6. P1. |
| 16 | FY.ÑO.007 | No explícito | Niños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑO.007.png); casilla 7. P1. |
| 16 | FY.ÑO.008 | No explícito | Niños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑO.008.png); casilla 8. P1. |
| 16 | FY.ÑO.009 | No explícito | Niños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑO.009.png); casilla 9. P1. La figura lleva un diploma; su texto no declara tamaño ni precio. |
| 17 | FY.ÑO.010 | No explícito | Niños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑO.010.png); casilla 1. P1. |
| 17 | FY.ÑO.011 | No explícito | Niños | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.ÑO.011.png); casilla 2. P1. |
| 18 | FY.OP.001 | No explícito | Oficios y profesiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.OP.001.png); casilla 1. P1. |
| 18 | FY.OP.002 | No explícito | Oficios y profesiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.OP.002.png); casilla 2. P1. |
| 18 | FY.OP.003 | No explícito | Oficios y profesiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.OP.003.png); casilla 3. P1. |
| 18 | FY.OP.004 | No explícito | Oficios y profesiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.OP.004.png); casilla 4. P1. |
| 18 | FY.OP.005 | No explícito | Oficios y profesiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.OP.005.png); casilla 5. P1. |
| 18 | FY.OP.006 | Maestra | Oficios y profesiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.OP.006.png); casilla 6. P1. |
| 18 | FY.OP.007 | No explícito | Oficios y profesiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.OP.007.png); casilla 7. P1. |
| 18 | FY.OP.008 | No explícito | Oficios y profesiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.OP.008.png); casilla 8. P1. La chaqueta lleva «CHEF» como parte del diseño, sin rótulo nominal separado. |
| 18 | FY.OP.009 | No explícito | Oficios y profesiones | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.OP.009.png); casilla 9. P1. |
| 19 | FY.PAQ.001 | No explícito | Paquetes | 6 (X6) | No declarada | No | [Imagen](../app/static/img/products/FY.PAQ.001.png); casilla 1. P1. «TÚ ELIGES LOS COLORES» (aviso de página). |
| 19 | FY.PAQ.002 | No explícito | Paquetes | 24 (X24) | No declarada | No | [Imagen](../app/static/img/products/FY.PAQ.002.png); casilla 2. P1. «TÚ ELIGES LOS COLORES» (aviso de página). |
| 19 | FY.PAQ.003 | No explícito | Paquetes | 5 (X5) | No declarada | No | [Imagen](../app/static/img/products/FY.PAQ.003.png); casilla 3. P1. «TÚ ELIGES LOS COLORES» (aviso de página). |
| 19 | FY.PAQ.004 | No explícito | Paquetes | 24 (X24) | No declarada | No | [Imagen](../app/static/img/products/FY.PAQ.004.png); casilla 4. P1. «TÚ ELIGES LOS COLORES» (aviso de página). |
| 19 | FY.PAQ.005 | No explícito | Paquetes | 20 (X20) | No declarada | No | [Imagen](../app/static/img/products/FY.PAQ.005.png); casilla 5. P1. «TÚ ELIGES LOS COLORES» (aviso de página). |
| 19 | FY.PAQ.006 | No explícito | Paquetes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PAQ.006.png); casilla 6. P1. «TÚ ELIGES LOS COLORES» (aviso de página). No extrapolar X20/X24 de las casillas vecinas ni contar piezas para inventar el contenido del paquete. |
| 20 | FY.PE.001 | No explícito | Peces | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PE.001.png); casilla 1. P1. |
| 20 | FY.PE.002 | No explícito | Peces | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PE.002.png); casilla 2. P1. |
| 20 | FY.PE.003 | No explícito | Peces | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PE.003.png); casilla 3. P1. |
| 20 | FY.PE.004 | No explícito | Peces | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PE.004.png); casilla 4. P1. |
| 20 | FY.PE.005 | No explícito | Peces | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PE.005.png); casilla 5. P1. |
| 20 | FY.PE.006 | No explícito | Peces | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PE.006.png); casilla 6. P1. |
| 21 | FY.PER.001 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.001.png); casilla 1. P1. |
| 21 | FY.PER.002 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.002.png); casilla 2. P1. |
| 21 | FY.PER.003 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.003.png); casilla 3. P1. |
| 21 | FY.PER.004 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.004.png); casilla 4. P1. |
| 21 | FY.PER.005 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.005.png); casilla 5. P1. El número 95 pertenece al diseño del automóvil; no es precio, cantidad de paquete ni medida. |
| 21 | FY.PER.006 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.006.png); casilla 6. P1. Letras en el libro de la figura; no constituyen información comercial de precio o medida. |
| 21 | FY.PER.007 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.007.png); casilla 7. P1. |
| 21 | FY.PER.008 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.008.png); casilla 8. P1. |
| 21 | FY.PER.009 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.009.png); casilla 9. P1. |
| 22 | FY.PER.010 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.010.png); casilla 1. P1. |
| 22 | FY.PER.011 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.011.png); casilla 2. P1. |
| 22 | FY.PER.012 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.012.png); casilla 3. P1. |
| 22 | FY.PER.013 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.013.png); casilla 4. P1. Fotografía sobre base de corte graduada, con números y marcas de unidad en el fondo. No hay una cota ni una medida declarada del producto; no se calcula tamaño a partir de la escala o los píxeles. |
| 22 | FY.PER.014 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.014.png); casilla 5. P1. |
| 22 | FY.PER.015 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.015.png); casilla 6. P1. |
| 22 | FY.PER.016 | No explícito | Personajes | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.PER.016.png); casilla 7. P1. |
| 23 | FY.RE.001 | No explícito | Religiosos | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.RE.001.png); casilla 1. P1. |
| 23 | FY.RE.002 | No explícito | Religiosos | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.RE.002.png); casilla 2. P1. |
| 23 | FY.RE.003 | No explícito | Religiosos | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.RE.003.png); casilla 3. P1. |
| 23 | FY.RE.004 | No explícito | Religiosos | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.RE.004.png); casilla 4. P1. |
| 23 | FY.RE.005 | No explícito | Religiosos | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.RE.005.png); casilla 5. P1. |
| 23 | FY.RE.006 | No explícito | Religiosos | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.RE.006.png); casilla 6. P1. |
| 23 | FY.RE.007 | Virgen de la Medalla Milagrosa | Religiosos | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.RE.007.png); casilla 7. P1. |
| 23 | FY.RE.008 | No explícito | Religiosos | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.RE.008.png); casilla 8. P1. |
| 23 | FY.RE.009 | No explícito | Religiosos | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.RE.009.png); casilla 9. P1. |
| 24 | FY.RE.010 | María | Religiosos | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.RE.010.png); casilla 1. P1. |
| 24 | FY.RE.011 | José | Religiosos | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.RE.011.png); casilla 2. P1. |
| 25 | FY.TOP.001 | No explícito | Toppers | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.TOP.001.png); casilla 1. P1. Texto del diseño: «Felicitaciones». Varias muestras de color, sin cantidad de paquete declarada. |
| 25 | FY.TOP.002 | No explícito | Toppers | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.TOP.002.png); casilla 2. P1. Texto del diseño: «Feliz Día Mamá». Varias muestras de color, sin cantidad de paquete declarada. |
| 25 | FY.TOP.003 | No explícito | Toppers | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.TOP.003.png); casilla 3. P1. Texto del diseño: «Feliz cumple». Varias muestras de color, sin cantidad de paquete declarada. |
| 25 | FY.TOP.004 | No explícito | Toppers | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.TOP.004.png); casilla 4. P1. Texto del diseño: «Feliz día». Varias muestras de color, sin cantidad de paquete declarada. |
| 26 | FY.VAR.001 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.001.png); casilla 1. P1. |
| 26 | FY.VAR.002 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.002.png); casilla 2. P1. |
| 26 | FY.VAR.003 | Identificativos | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.003.png); casilla 3. P1. |
| 26 | FY.VAR.004 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.004.png); casilla 4. P1. |
| 26 | FY.VAR.005 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.005.png); casilla 5. P1. |
| 26 | FY.VAR.006 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.006.png); casilla 6. P1. |
| 26 | FY.VAR.007 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.007.png); casilla 7. P1. |
| 26 | FY.VAR.008 | Ciclo del agua | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.008.png); casilla 8. P1. |
| 26 | FY.VAR.009 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.009.png); casilla 9. P1. Texto del diseño: «POLICÍA»; no es un rótulo nominal de catálogo separado. |
| 27 | FY.VAR.010 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.010.png); casilla 1. P1. |
| 27 | FY.VAR.011 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.011.png); casilla 2. P1. |
| 27 | FY.VAR.012 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.012.png); casilla 3. P1. Texto del diseño: «Feliz día». |
| 27 | FY.VAR.013 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.013.png); casilla 4. P1. |
| 27 | FY.VAR.014 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.014.png); casilla 5. P1. Nombres geográficos dentro del mapa; no son medidas ni precios. |
| 27 | FY.VAR.015 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.015.png); casilla 6. P1. |
| 27 | FY.VAR.016 | Identificativos | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.016.png); casilla 7. P1. |
| 27 | FY.VAR.017 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.017.png); casilla 8. P1. |
| 27 | FY.VAR.018 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.018.png); casilla 9. P1. |
| 28 | FY.VAR.019 | No explícito | Varios | No indicada | No declarada | No | [Imagen](../app/static/img/products/FY.VAR.019.png); casilla 1. P1. Imagen parcial, sin nombre explícito: se conserva el producto sin inventar una identificación. |

## Carátulas sin código y páginas no comerciales

Las nueve carátulas siguen fuera de los 173 productos publicados. Se transcriben sus textos de diseño para distinguir las imágenes; no se les asignan códigos, medidas, precios ni nuevos nombres comerciales. No se recupera ni se transcribe información cubierta por los recuadros «CENSORED» del PDF.

| Página | Código | Nombre | Categoría | Cantidad/paquete | Medida explícita | Precio explícito | Observaciones |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 29 | Sin código | No explícito | Carátulas | No indicada | No declarada | No | [Imagen](../app/static/img/products/uncoded-page-29-slot-01.png); casilla 1. Texto del diseño: «Ciencias naturales · Resúmenes». P1; precio según diseño. |
| 29 | Sin código | No explícito | Carátulas | No indicada | No declarada | No | [Imagen](../app/static/img/products/uncoded-page-29-slot-02.png); casilla 2. Texto del diseño: «Matemática · Resúmenes». P1; precio según diseño. |
| 29 | Sin código | No explícito | Carátulas | No indicada | No declarada | No | [Imagen](../app/static/img/products/uncoded-page-29-slot-03.png); casilla 3. Texto del diseño: «Tareas en clase y deberes de Matemática». P1; precio según diseño. |
| 29 | Sin código | No explícito | Carátulas | No indicada | No declarada | No | [Imagen](../app/static/img/products/uncoded-page-29-slot-04.png); casilla 4. Texto del diseño: «Lengua y literatura · Resúmenes». P1; precio según diseño. |
| 29 | Sin código | No explícito | Carátulas | No indicada | No declarada | No | [Imagen](../app/static/img/products/uncoded-page-29-slot-05.png); casilla 5. Texto del diseño: «Tareas varias». P1; precio según diseño. |
| 29 | Sin código | No explícito | Carátulas | No indicada | No declarada | No | [Imagen](../app/static/img/products/uncoded-page-29-slot-06.png); casilla 6. Texto del diseño: «Ejercicios caligráficos». P1; precio según diseño. |
| 29 | Sin código | No explícito | Carátulas | No indicada | No declarada | No | [Imagen](../app/static/img/products/uncoded-page-29-slot-07.png); casilla 7. Texto del diseño: «Apuntes». P1; precio según diseño. |
| 29 | Sin código | No explícito | Carátulas | No indicada | No declarada | No | [Imagen](../app/static/img/products/uncoded-page-29-slot-08.png); casilla 8. Texto del diseño: «Cívica». P1; precio según diseño. |
| 29 | Sin código | No explícito | Carátulas | No indicada | No declarada | No | [Imagen](../app/static/img/products/uncoded-page-29-slot-09.png); casilla 9. Texto del diseño: «Estudios sociales». P1; precio según diseño. |
| 1 | No aplica | No aplica | Portada | No aplica | No declarada | No | Logotipo, contacto y texto P1; no es un producto. |
| 30 | No aplica | No aplica | Cierre | No aplica | No declarada | No | Llamado a consultar y teléfonos; no es un producto. |
| 31 | FY.AN.001 repetido 9 veces | No explícito | Rectángulos | No indicada | No declarada | No | Nueve logotipos de plantilla, no nueve productos ni variantes del animal de la página 2. |
| 32 | FY.TOP.001 repetido 9 veces | No explícito | Cuadrado | No indicada | No declarada | No | Nueve logotipos de plantilla, no variantes del topper de la página 25. |
| 33 | FY.CAR.001 y FY.CAR.002 | No explícito | Rectángulo horizontal | No indicada | No declarada | No | Dos logotipos con código no cero y siete FY.CAR.000; plantilla excluida, sin nuevas variantes de los carteles de la página 8. |

Las otras casillas .000 de las páginas 6–28 están contabilizadas por página en la tabla de cobertura: muestran el logotipo y no son productos. No se añaden al catálogo.

## Aplicación a la tienda y asignación administrativa

La tienda debe presentar «Precio según tamaño» / «Solicitar cotización», conservar el campo de tamaño libre y reunir código, cantidad, tamaño solicitado y personalización en una solicitud. No se ofrecen tamaños prefijados que el PDF no declara, ni se publica precio cero como sustituto de un precio desconocido.

Los importes de costos, recetas y cálculos guardados son sugerencias administrativas. No son una lista oficial de precios ni se publican en fichas, tarjetas, favoritos, API pública o solicitudes por el hecho de existir una receta.

El administrador puede asignar un precio real en **Cotizaciones → Nueva cotización**, indicando el tamaño y la personalización en cada línea y escribiendo el precio manual antes de IVA acordado por el negocio. Un mismo código puede tener líneas separadas para distintos tamaños, con precios independientes. Puede usar una receta/cálculo como referencia de costos o registrar el costo real manual; no debe inventar el costo faltante. La cotización conserva tamaño, precio y snapshot; los documentos históricos no se recalculan. Asignar ese precio en una propuesta no lo convierte en precio oficial para todos los tamaños ni lo publica en el catálogo. Esta tarea no crea una tarifa por variantes ni rellena precios o costos administrativos.

No se reimporta el catálogo ni se actualiza la base local para esta auditoría. Permanecen intactos los 173 productos, sus códigos, categorías e imágenes, las exclusiones y el historial comercial.
