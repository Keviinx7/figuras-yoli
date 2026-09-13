# Auditoría del catálogo oficial — Yoli Figuras de Fomix

Fuente de verdad: `docs/catalogo-productos.pdf` (33 páginas, Canva). SHA-256 del PDF: `52d58526c7c3ae074abe0cb6a8fe9656da0780e7b6c3cdaafbb52b2a1c7766bc`.
Base comparada: `instance/tienda.db` (mutación del 2026-09-13 que añade una configuración de impuesto; los 173 productos no fueron reimportados en esta auditoría).
Verificación realizada sin reimportar el catálogo ni modificar productos: los recortes de la base se compararon con el manifiesto original (`catalog-audit/manifest.json`), con un render independiente del PDF y celda por celda.

## Cómo se verificó cada punto

| Requisito | Método | Resultado |
|---|---|---|
| Página y código de origen | Manifiesto de extracción (página/casilla), texto del PDF | 173/173 |
| Nombre explícito del PDF | Rótulos impresos transcritos (23) | 23/23 coinciden con la tienda |
| Nombre inferido permitido | Solo cuando el PDF no imprime rótulo nominal | 149 |
| Categoría | Mapeo prefijo→categoría del catálogo | 173/173 |
| Imagen asociada | SHA-256 idéntico al manifiesto | 173/173 |
| Imagen no del vecino | Coincidencia de celda en render independiente (mejor ajuste entre las 9 casillas) | 173/173 |
| Duplicados | Códigos únicos en `products` y en el manifiesto | 0 |
| Faltan productos | Códigos del PDF ausentes en la base | 0 |
| Sobran públicos | Códigos de la base ausentes en el PDF | 0 |
| Ñ exactas | Igualdad de cadenas `FY.ÑA.*`/`FY.ÑO.*` (28) | 28/28 |
| .000 comerciales | Excluidos 77; ningún código de la base termina en `.000` (constraint `no_placeholder`) | 0 |
| Códigos inventados | 9 carátulas sin código no están en la base y conservan su nombre de casilla | 0 |

## Tabla completa (173 productos)

| Página PDF | Código | Nombre PDF | Nombre tienda | Categoría | Imagen | Estado | Observación |
| 2 | [FY.AN.001](../../app/static/img/products/FY.AN.001.png) | — | Gato | Animales | `FY.AN.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 2 | [FY.AN.002](../../app/static/img/products/FY.AN.002.png) | — | Gallina | Animales | `FY.AN.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 2 | [FY.AN.003](../../app/static/img/products/FY.AN.003.png) | — | Perro | Animales | `FY.AN.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 2 | [FY.AN.004](../../app/static/img/products/FY.AN.004.png) | — | Caballo | Animales | `FY.AN.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 2 | [FY.AN.005](../../app/static/img/products/FY.AN.005.png) | — | Pato | Animales | `FY.AN.005.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 2 | [FY.AN.006](../../app/static/img/products/FY.AN.006.png) | — | Pato sentado | Animales | `FY.AN.006.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 2 | [FY.AN.007](../../app/static/img/products/FY.AN.007.png) | — | Roedor | Animales | `FY.AN.007.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 2 | [FY.AN.008](../../app/static/img/products/FY.AN.008.png) | — | Capibara con bebida | Animales | `FY.AN.008.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 2 | [FY.AN.009](../../app/static/img/products/FY.AN.009.png) | — | Capibara con sandía | Animales | `FY.AN.009.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 3 | [FY.AN.010](../../app/static/img/products/FY.AN.010.png) | — | Caracol | Animales | `FY.AN.010.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 3 | [FY.AN.011](../../app/static/img/products/FY.AN.011.png) | — | Cocodrilo | Animales | `FY.AN.011.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 3 | [FY.AN.012](../../app/static/img/products/FY.AN.012.png) | — | Elefante | Animales | `FY.AN.012.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 3 | [FY.AN.013](../../app/static/img/products/FY.AN.013.png) | — | Oruga | Animales | `FY.AN.013.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 3 | [FY.AN.014](../../app/static/img/products/FY.AN.014.png) | — | Ardilla | Animales | `FY.AN.014.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 3 | [FY.AN.015](../../app/static/img/products/FY.AN.015.png) | — | Hormiga | Animales | `FY.AN.015.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 3 | [FY.AN.016](../../app/static/img/products/FY.AN.016.png) | — | Jirafa | Animales | `FY.AN.016.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 3 | [FY.AN.017](../../app/static/img/products/FY.AN.017.png) | — | León | Animales | `FY.AN.017.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 3 | [FY.AN.018](../../app/static/img/products/FY.AN.018.png) | — | Mariposa | Animales | `FY.AN.018.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 4 | [FY.AN.019](../../app/static/img/products/FY.AN.019.png) | — | Mariquita | Animales | `FY.AN.019.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 4 | [FY.AN.020](../../app/static/img/products/FY.AN.020.png) | — | Mono | Animales | `FY.AN.020.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 4 | [FY.AN.021](../../app/static/img/products/FY.AN.021.png) | — | Oso saludando | Animales | `FY.AN.021.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 4 | [FY.AN.022](../../app/static/img/products/FY.AN.022.png) | — | Oso sentado | Animales | `FY.AN.022.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 4 | [FY.AN.023](../../app/static/img/products/FY.AN.023.png) | — | Panda | Animales | `FY.AN.023.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 4 | [FY.AN.024](../../app/static/img/products/FY.AN.024.png) | — | Pelícano | Animales | `FY.AN.024.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 4 | [FY.AN.025](../../app/static/img/products/FY.AN.025.png) | — | Pollito | Animales | `FY.AN.025.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 4 | [FY.AN.026](../../app/static/img/products/FY.AN.026.png) | — | Insecto verde | Animales | `FY.AN.026.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 4 | [FY.AN.027](../../app/static/img/products/FY.AN.027.png) | — | Rana | Animales | `FY.AN.027.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 5 | [FY.AN.028](../../app/static/img/products/FY.AN.028.png) | — | Serpiente | Animales | `FY.AN.028.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 5 | [FY.AN.029](../../app/static/img/products/FY.AN.029.png) | — | Tortuga | Animales | `FY.AN.029.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 5 | [FY.AN.030](../../app/static/img/products/FY.AN.030.png) | — | Tigre | Animales | `FY.AN.030.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 5 | [FY.AN.031](../../app/static/img/products/FY.AN.031.png) | — | Cebra | Animales | `FY.AN.031.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 5 | [FY.AN.032](../../app/static/img/products/FY.AN.032.png) | — | Vaca | Animales | `FY.AN.032.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 5 | [FY.AN.033](../../app/static/img/products/FY.AN.033.png) | — | Loro | Animales | `FY.AN.033.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 5 | [FY.AN.034](../../app/static/img/products/FY.AN.034.png) | — | Dinosaurio | Animales | `FY.AN.034.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 5 | [FY.AN.035](../../app/static/img/products/FY.AN.035.png) | — | Unicornio | Animales | `FY.AN.035.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 5 | [FY.AN.036](../../app/static/img/products/FY.AN.036.png) | — | Cerdo | Animales | `FY.AN.036.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 6 | [FY.AN.037](../../app/static/img/products/FY.AN.037.png) | — | Paloma | Animales | `FY.AN.037.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 6 | [FY.AN.038](../../app/static/img/products/FY.AN.038.png) | — | Conejo | Animales | `FY.AN.038.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 7 | [FY.CD.001](../../app/static/img/products/FY.CD.001.png) | — | Niño con bastón y gafas | Capacidades diferentes | `FY.CD.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 8 | [FY.CAR.001](../../app/static/img/products/FY.CAR.001.png) | — | Bienvenidos al año lectivo | Carteles | `FY.CAR.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 8 | [FY.CAR.002](../../app/static/img/products/FY.CAR.002.png) | — | Banderín de bienvenida | Carteles | `FY.CAR.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 8 | [FY.CAR.003](../../app/static/img/products/FY.CAR.003.png) | — | Bienvenidos al nuevo año lectivo | Carteles | `FY.CAR.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 8 | [FY.CAR.004](../../app/static/img/products/FY.CAR.004.png) | — | Bienvenida con nombre de profesora | Carteles | `FY.CAR.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 8 | [FY.CAR.005](../../app/static/img/products/FY.CAR.005.png) | — | Banderín con nombre de profesora | Carteles | `FY.CAR.005.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 9 | [FY.CH.001](../../app/static/img/products/FY.CH.001.png) | Digestivo | Digestivo | Cuerpo humano y células | `FY.CH.001.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 9 | [FY.CH.002](../../app/static/img/products/FY.CH.002.png) | Circulatorio | Circulatorio | Cuerpo humano y células | `FY.CH.002.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 9 | [FY.CH.003](../../app/static/img/products/FY.CH.003.png) | Endocrino | Endocrino | Cuerpo humano y células | `FY.CH.003.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 9 | [FY.CH.004](../../app/static/img/products/FY.CH.004.png) | Nervioso | Nervioso | Cuerpo humano y células | `FY.CH.004.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 9 | [FY.CH.005](../../app/static/img/products/FY.CH.005.png) | Respiratorio | Respiratorio | Cuerpo humano y células | `FY.CH.005.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 9 | [FY.CH.006](../../app/static/img/products/FY.CH.006.png) | Reproductor femenino | Reproductor femenino | Cuerpo humano y células | `FY.CH.006.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 9 | [FY.CH.007](../../app/static/img/products/FY.CH.007.png) | Reproductor masculino | Reproductor masculino | Cuerpo humano y células | `FY.CH.007.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 9 | [FY.CH.008](../../app/static/img/products/FY.CH.008.png) | — | Esqueleto humano | Cuerpo humano y células | `FY.CH.008.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 9 | [FY.CH.009](../../app/static/img/products/FY.CH.009.png) | — | Cerebro | Cuerpo humano y células | `FY.CH.009.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 10 | [FY.CH.010](../../app/static/img/products/FY.CH.010.png) | — | Corazón humano | Cuerpo humano y células | `FY.CH.010.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 10 | [FY.CH.011](../../app/static/img/products/FY.CH.011.png) | Célula animal | Célula animal | Cuerpo humano y células | `FY.CH.011.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 10 | [FY.CH.012](../../app/static/img/products/FY.CH.012.png) | Célula procariota | Célula procariota | Cuerpo humano y células | `FY.CH.012.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 10 | [FY.CH.013](../../app/static/img/products/FY.CH.013.png) | Célula vegetal | Célula vegetal | Cuerpo humano y células | `FY.CH.013.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 11 | [FY.ER.001](../../app/static/img/products/FY.ER.001.png) | — | Pareja con tocados de plumas | Etnias y regiones | `FY.ER.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 11 | [FY.ER.002](../../app/static/img/products/FY.ER.002.png) | — | Pareja con pañuelo y falda | Etnias y regiones | `FY.ER.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 11 | [FY.ER.003](../../app/static/img/products/FY.ER.003.png) | — | Pareja con sombreros | Etnias y regiones | `FY.ER.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 11 | [FY.ER.004](../../app/static/img/products/FY.ER.004.png) | — | Pareja con pañuelos amarillos | Etnias y regiones | `FY.ER.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 12 | [FY.IM.001](../../app/static/img/products/FY.IM.001.png) | — | Bajo eléctrico | Instrumentos musicales | `FY.IM.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 12 | [FY.IM.002](../../app/static/img/products/FY.IM.002.png) | — | Guitarra | Instrumentos musicales | `FY.IM.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 12 | [FY.IM.003](../../app/static/img/products/FY.IM.003.png) | — | Maracas | Instrumentos musicales | `FY.IM.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 12 | [FY.IM.004](../../app/static/img/products/FY.IM.004.png) | — | Saxofón | Instrumentos musicales | `FY.IM.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 12 | [FY.IM.005](../../app/static/img/products/FY.IM.005.png) | — | Tambor | Instrumentos musicales | `FY.IM.005.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 12 | [FY.IM.006](../../app/static/img/products/FY.IM.006.png) | — | Violín | Instrumentos musicales | `FY.IM.006.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 12 | [FY.IM.007](../../app/static/img/products/FY.IM.007.png) | — | Arpa | Instrumentos musicales | `FY.IM.007.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 13 | [FY.NAV.001](../../app/static/img/products/FY.NAV.001.png) | Melchor | Melchor | Navideños | `FY.NAV.001.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 13 | [FY.NAV.002](../../app/static/img/products/FY.NAV.002.png) | Baltazar | Baltazar | Navideños | `FY.NAV.002.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 13 | [FY.NAV.003](../../app/static/img/products/FY.NAV.003.png) | Gaspar | Gaspar | Navideños | `FY.NAV.003.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 13 | [FY.NAV.004](../../app/static/img/products/FY.NAV.004.png) | Bota navideña | Bota navideña | Navideños | `FY.NAV.004.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 13 | [FY.NAV.005](../../app/static/img/products/FY.NAV.005.png) | Reno navideño | Reno navideño | Navideños | `FY.NAV.005.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 13 | [FY.NAV.006](../../app/static/img/products/FY.NAV.006.png) | Muñeco de nieve | Muñeco de nieve | Navideños | `FY.NAV.006.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 14 | [FY.ÑA.001](../../app/static/img/products/FY.ÑA.001.png) | — | Niña con lápiz y manzana | Niñas | `FY.ÑA.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 14 | [FY.ÑA.002](../../app/static/img/products/FY.ÑA.002.png) | — | Niña con libro azul | Niñas | `FY.ÑA.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 14 | [FY.ÑA.003](../../app/static/img/products/FY.ÑA.003.png) | — | Niña con lápiz y cuaderno | Niñas | `FY.ÑA.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 14 | [FY.ÑA.004](../../app/static/img/products/FY.ÑA.004.png) | — | Niña con vestido rosa | Niñas | `FY.ÑA.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 14 | [FY.ÑA.005](../../app/static/img/products/FY.ÑA.005.png) | — | Niña sentada leyendo | Niñas | `FY.ÑA.005.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 14 | [FY.ÑA.006](../../app/static/img/products/FY.ÑA.006.png) | — | Niña abrazando un lápiz | Niñas | `FY.ÑA.006.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 14 | [FY.ÑA.007](../../app/static/img/products/FY.ÑA.007.png) | — | Niña escribiendo | Niñas | `FY.ÑA.007.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 14 | [FY.ÑA.008](../../app/static/img/products/FY.ÑA.008.png) | — | Niña con delantal y manzana | Niñas | `FY.ÑA.008.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 14 | [FY.ÑA.009](../../app/static/img/products/FY.ÑA.009.png) | — | Niña con brazos abiertos | Niñas | `FY.ÑA.009.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 15 | [FY.ÑA.010](../../app/static/img/products/FY.ÑA.010.png) | — | Niña con libros | Niñas | `FY.ÑA.010.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 15 | [FY.ÑA.012](../../app/static/img/products/FY.ÑA.012.png) | — | Niña con libro rojo | Niñas | `FY.ÑA.012.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 15 | [FY.ÑA.013](../../app/static/img/products/FY.ÑA.013.png) | — | Niña con vestido y diadema | Niñas | `FY.ÑA.013.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 15 | [FY.ÑA.014](../../app/static/img/products/FY.ÑA.014.png) | — | Niña graduada | Niñas | `FY.ÑA.014.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 15 | [FY.ÑA.015](../../app/static/img/products/FY.ÑA.015.png) | — | Niña con cuaderno y lazo | Niñas | `FY.ÑA.015.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 15 | [FY.ÑA.016](../../app/static/img/products/FY.ÑA.016.png) | — | Niña leyendo un libro rojo | Niñas | `FY.ÑA.016.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 15 | [FY.ÑA.017](../../app/static/img/products/FY.ÑA.017.png) | — | Niña con cuerda de saltar | Niñas | `FY.ÑA.017.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 15 | [FY.ÑA.018](../../app/static/img/products/FY.ÑA.018.png) | — | Niña con overol y lápiz | Niñas | `FY.ÑA.018.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 16 | [FY.ÑO.001](../../app/static/img/products/FY.ÑO.001.png) | — | Niño con camiseta roja | Niños | `FY.ÑO.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 16 | [FY.ÑO.002](../../app/static/img/products/FY.ÑO.002.png) | — | Niño con libro amarillo | Niños | `FY.ÑO.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 16 | [FY.ÑO.003](../../app/static/img/products/FY.ÑO.003.png) | — | Niño con libro en la mano | Niños | `FY.ÑO.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 16 | [FY.ÑO.004](../../app/static/img/products/FY.ÑO.004.png) | — | Niño en patineta | Niños | `FY.ÑO.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 16 | [FY.ÑO.005](../../app/static/img/products/FY.ÑO.005.png) | — | Niño saludando | Niños | `FY.ÑO.005.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 16 | [FY.ÑO.006](../../app/static/img/products/FY.ÑO.006.png) | — | Niño con overol azul | Niños | `FY.ÑO.006.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 16 | [FY.ÑO.007](../../app/static/img/products/FY.ÑO.007.png) | — | Niño leyendo un libro verde | Niños | `FY.ÑO.007.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 16 | [FY.ÑO.008](../../app/static/img/products/FY.ÑO.008.png) | — | Niño con mochila | Niños | `FY.ÑO.008.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 16 | [FY.ÑO.009](../../app/static/img/products/FY.ÑO.009.png) | — | Niño graduado | Niños | `FY.ÑO.009.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 17 | [FY.ÑO.010](../../app/static/img/products/FY.ÑO.010.png) | — | Niño con balón de fútbol | Niños | `FY.ÑO.010.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 17 | [FY.ÑO.011](../../app/static/img/products/FY.ÑO.011.png) | — | Niño con lápiz | Niños | `FY.ÑO.011.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 18 | [FY.OP.001](../../app/static/img/products/FY.OP.001.png) | — | Bombero | Oficios y profesiones | `FY.OP.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 18 | [FY.OP.002](../../app/static/img/products/FY.OP.002.png) | — | Mecánico | Oficios y profesiones | `FY.OP.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 18 | [FY.OP.003](../../app/static/img/products/FY.OP.003.png) | — | Policía con uniforme verde | Oficios y profesiones | `FY.OP.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 18 | [FY.OP.004](../../app/static/img/products/FY.OP.004.png) | — | Enfermera con uniforme blanco | Oficios y profesiones | `FY.OP.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 18 | [FY.OP.005](../../app/static/img/products/FY.OP.005.png) | — | Enfermera con uniforme azul | Oficios y profesiones | `FY.OP.005.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 18 | [FY.OP.006](../../app/static/img/products/FY.OP.006.png) | Maestra | Maestra | Oficios y profesiones | `FY.OP.006.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 18 | [FY.OP.007](../../app/static/img/products/FY.OP.007.png) | — | Policía con radio | Oficios y profesiones | `FY.OP.007.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 18 | [FY.OP.008](../../app/static/img/products/FY.OP.008.png) | — | Cocinero | Oficios y profesiones | `FY.OP.008.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 18 | [FY.OP.009](../../app/static/img/products/FY.OP.009.png) | — | Carpintero | Oficios y profesiones | `FY.OP.009.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 19 | [FY.PAQ.001](../../app/static/img/products/FY.PAQ.001.png) | — | Paquete de útiles escolares | Paquetes | `FY.PAQ.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 19 | [FY.PAQ.002](../../app/static/img/products/FY.PAQ.002.png) | — | Paquete de estrellas | Paquetes | `FY.PAQ.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 19 | [FY.PAQ.003](../../app/static/img/products/FY.PAQ.003.png) | — | Paquete de los cinco sentidos | Paquetes | `FY.PAQ.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 19 | [FY.PAQ.004](../../app/static/img/products/FY.PAQ.004.png) | — | Paquete de corazones | Paquetes | `FY.PAQ.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 19 | [FY.PAQ.005](../../app/static/img/products/FY.PAQ.005.png) | — | Paquete de flores | Paquetes | `FY.PAQ.005.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 19 | [FY.PAQ.006](../../app/static/img/products/FY.PAQ.006.png) | — | Paquete de huellas y huesos | Paquetes | `FY.PAQ.006.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 20 | [FY.PE.001](../../app/static/img/products/FY.PE.001.png) | — | Pez azul y amarillo | Peces | `FY.PE.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 20 | [FY.PE.002](../../app/static/img/products/FY.PE.002.png) | — | Pez verde y rosa | Peces | `FY.PE.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 20 | [FY.PE.003](../../app/static/img/products/FY.PE.003.png) | — | Pez naranja y amarillo | Peces | `FY.PE.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 20 | [FY.PE.004](../../app/static/img/products/FY.PE.004.png) | — | Pez amarillo y verde | Peces | `FY.PE.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 20 | [FY.PE.005](../../app/static/img/products/FY.PE.005.png) | — | Pez azul | Peces | `FY.PE.005.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 20 | [FY.PE.006](../../app/static/img/products/FY.PE.006.png) | — | Pez naranja con franjas blancas | Peces | `FY.PE.006.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 21 | [FY.PER.001](../../app/static/img/products/FY.PER.001.png) | — | Oso con vaso | Personajes | `FY.PER.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 21 | [FY.PER.002](../../app/static/img/products/FY.PER.002.png) | — | Criatura azul de orejas grandes | Personajes | `FY.PER.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 21 | [FY.PER.003](../../app/static/img/products/FY.PER.003.png) | — | Erizo azul | Personajes | `FY.PER.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 21 | [FY.PER.004](../../app/static/img/products/FY.PER.004.png) | — | Superhéroe con telarañas | Personajes | `FY.PER.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 21 | [FY.PER.005](../../app/static/img/products/FY.PER.005.png) | — | Auto de carreras rojo | Personajes | `FY.PER.005.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 21 | [FY.PER.006](../../app/static/img/products/FY.PER.006.png) | — | Perro con libro | Personajes | `FY.PER.006.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 21 | [FY.PER.007](../../app/static/img/products/FY.PER.007.png) | — | Niño con traje rojo | Personajes | `FY.PER.007.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 21 | [FY.PER.008](../../app/static/img/products/FY.PER.008.png) | — | Gatita con flor | Personajes | `FY.PER.008.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 21 | [FY.PER.009](../../app/static/img/products/FY.PER.009.png) | — | Hada con vestido verde | Personajes | `FY.PER.009.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 22 | [FY.PER.010](../../app/static/img/products/FY.PER.010.png) | — | Perro bombero con cartel | Personajes | `FY.PER.010.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 22 | [FY.PER.011](../../app/static/img/products/FY.PER.011.png) | — | Perro policía con cartel | Personajes | `FY.PER.011.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 22 | [FY.PER.012](../../app/static/img/products/FY.PER.012.png) | — | Perro constructor con cartel | Personajes | `FY.PER.012.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 22 | [FY.PER.013](../../app/static/img/products/FY.PER.013.png) | — | Ratona con lazo rojo | Personajes | `FY.PER.013.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 22 | [FY.PER.014](../../app/static/img/products/FY.PER.014.png) | — | Cara de perro policía | Personajes | `FY.PER.014.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 22 | [FY.PER.015](../../app/static/img/products/FY.PER.015.png) | — | Cara de perro bombero | Personajes | `FY.PER.015.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 22 | [FY.PER.016](../../app/static/img/products/FY.PER.016.png) | — | Cara de perro constructor | Personajes | `FY.PER.016.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 23 | [FY.RE.001](../../app/static/img/products/FY.RE.001.png) | — | Sacerdote | Religiosos | `FY.RE.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 23 | [FY.RE.002](../../app/static/img/products/FY.RE.002.png) | — | Ángel con alas rosas | Religiosos | `FY.RE.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 23 | [FY.RE.003](../../app/static/img/products/FY.RE.003.png) | — | Ángel con alas azules | Religiosos | `FY.RE.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 23 | [FY.RE.004](../../app/static/img/products/FY.RE.004.png) | — | Hombre con túnica | Religiosos | `FY.RE.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 23 | [FY.RE.005](../../app/static/img/products/FY.RE.005.png) | — | Monja con rosario | Religiosos | `FY.RE.005.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 23 | [FY.RE.006](../../app/static/img/products/FY.RE.006.png) | — | Virgen con manto verde | Religiosos | `FY.RE.006.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 23 | [FY.RE.007](../../app/static/img/products/FY.RE.007.png) | Virgen de la Medalla Milagrosa | Virgen de la Medalla Milagrosa | Religiosos | `FY.RE.007.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 23 | [FY.RE.008](../../app/static/img/products/FY.RE.008.png) | — | Virgen con manto azul | Religiosos | `FY.RE.008.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 23 | [FY.RE.009](../../app/static/img/products/FY.RE.009.png) | — | Bebé en pesebre | Religiosos | `FY.RE.009.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 24 | [FY.RE.010](../../app/static/img/products/FY.RE.010.png) | María | María | Religiosos | `FY.RE.010.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 24 | [FY.RE.011](../../app/static/img/products/FY.RE.011.png) | José | José | Religiosos | `FY.RE.011.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 25 | [FY.TOP.001](../../app/static/img/products/FY.TOP.001.png) | — | Topper Felicitaciones | Toppers | `FY.TOP.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 25 | [FY.TOP.002](../../app/static/img/products/FY.TOP.002.png) | — | Topper Feliz Día Mamá | Toppers | `FY.TOP.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 25 | [FY.TOP.003](../../app/static/img/products/FY.TOP.003.png) | — | Topper Feliz Cumple | Toppers | `FY.TOP.003.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 25 | [FY.TOP.004](../../app/static/img/products/FY.TOP.004.png) | — | Topper Feliz Día | Toppers | `FY.TOP.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 26 | [FY.VAR.001](../../app/static/img/products/FY.VAR.001.png) | — | Mazo de juez | Varios | `FY.VAR.001.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 26 | [FY.VAR.002](../../app/static/img/products/FY.VAR.002.png) | — | Frasco con pastillas | Varios | `FY.VAR.002.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 26 | [FY.VAR.003](../../app/static/img/products/FY.VAR.003.png) | Identificativos | Identificativos | Varios | `FY.VAR.003.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 26 | [FY.VAR.004](../../app/static/img/products/FY.VAR.004.png) | — | Volcán | Varios | `FY.VAR.004.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 26 | [FY.VAR.005](../../app/static/img/products/FY.VAR.005.png) | — | Estetoscopio | Varios | `FY.VAR.005.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 26 | [FY.VAR.006](../../app/static/img/products/FY.VAR.006.png) | — | Planeta Tierra en una mano | Varios | `FY.VAR.006.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 26 | [FY.VAR.007](../../app/static/img/products/FY.VAR.007.png) | — | Esposas | Varios | `FY.VAR.007.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 26 | [FY.VAR.008](../../app/static/img/products/FY.VAR.008.png) | Ciclo del agua | Ciclo del agua | Varios | `FY.VAR.008.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 26 | [FY.VAR.009](../../app/static/img/products/FY.VAR.009.png) | — | Chaleco de policía | Varios | `FY.VAR.009.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 27 | [FY.VAR.010](../../app/static/img/products/FY.VAR.010.png) | — | Botiquín | Varios | `FY.VAR.010.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 27 | [FY.VAR.011](../../app/static/img/products/FY.VAR.011.png) | — | Bandera tricolor | Varios | `FY.VAR.011.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 27 | [FY.VAR.012](../../app/static/img/products/FY.VAR.012.png) | — | Animal con cartel Feliz Día | Varios | `FY.VAR.012.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 27 | [FY.VAR.013](../../app/static/img/products/FY.VAR.013.png) | — | Iglesia | Varios | `FY.VAR.013.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 27 | [FY.VAR.014](../../app/static/img/products/FY.VAR.014.png) | — | Mapa del Ecuador | Varios | `FY.VAR.014.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 27 | [FY.VAR.015](../../app/static/img/products/FY.VAR.015.png) | — | Casa | Varios | `FY.VAR.015.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 27 | [FY.VAR.016](../../app/static/img/products/FY.VAR.016.png) | Identificativos | Identificativos | Varios | `FY.VAR.016.png` | OK | Nombre explícito impreso en el PDF; coincide exactamente con la tienda. |
| 27 | [FY.VAR.017](../../app/static/img/products/FY.VAR.017.png) | — | Cerdo con órganos internos | Varios | `FY.VAR.017.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 27 | [FY.VAR.018](../../app/static/img/products/FY.VAR.018.png) | — | Anatomía interna del cerdo | Varios | `FY.VAR.018.png` | OK | Sin rótulo nominal impreso; nombre descriptivo inferido de la figura (permitido por la regla de autoridad). |
| 28 | [FY.VAR.019](../../app/static/img/products/FY.VAR.019.png) | — | — | Varios | `FY.VAR.019.png` | REVISIÓN HUMANA | Evidencia visual insuficiente para un nombre; se conserva el código con nombre vacío. |

## Resumen final
- Productos codificados en el PDF: **173**.
- Productos en la base: **173**.
- Coinciden exactamente (código + imagen + categoría): **173/173**.
- Discrepancias actuales: **0** (FY.CH.003 ya fue corregido a «Endocrino» en la base; ver observación).
- Faltan en la web: **0**.
- Sobran en la web: **0**.
- Nombres explícitos del PDF: **23** (22 conservados + 1 corregido: FY.CH.003 Endocrino).
- Nombres inferidos/descriptivos: **149**.
- Pendientes de revisión humana: **1** (FY.VAR.019, sin nombre por evidencia insuficiente).
- Imágenes asociadas correctamente: **173/173** (sha idéntico al manifiesto y mejor coincidencia en su propia celda).
- Códigos con Ñ: **28** (FY.ÑA.* y FY.ÑO.*) exactos.
- Excluidos deliberadamente (no productos, no en la web): **77** casillas `.000`; **9** carátulas de la página 29 sin código comercial; **20** casillas de logotipo de páginas 31–33 con códigos no nulos que no representan fotografías reales.

## Notas de fidelidad
- El rótulo explícito manda sobre la interpretación visual (ej. FY.CH.003 «Endocrino»).
- En carteles, toppers y paquetes no se contaron frases de diseño («Bienvenidos…», «Feliz Día…», «POLICIA», «DIPLOMA», «X6») como nombres nominales; la tienda usa nombres descriptivos. Los 9 carátulas de la página 29 no recibieron códigos inventados.
- Normalización tipográfica conservada: «Muñeco de nieve» frente al «Muneco de neive» impreso en FY.NAV.006.
- Validación visual en navegador (tras esta auditoría, base sin cambios): **89/89** comprobaciones públicas y **40/40** comerciales aprobadas (fotos por código, nombres, búsqueda, filtros, favoritos, carrito, cotización). No hay imágenes cruzadas, placeholders `.000` ni productos sin imagen.

_Informe generado el 2026-09-13 desde el manifiesto de extracción y la base actual. Sin commit; sin reimportación; sin borrado._