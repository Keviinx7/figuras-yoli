"""Record the manual visual review; update only the name column of the existing CSV."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader((ROOT / 'docs/name-review/before.csv').open()))
names = {}

def group(prefix, labels, start=1):
    for number, label in enumerate(labels.split('|'), start):
        names[f'FY.{prefix}.{number:03d}'] = label

group('AN', 'Gato|Gallina|Perro|Caballo|Pato|Pato sentado|Roedor|Capibara con bebida|Capibara con sandía|Caracol|Cocodrilo|Elefante|Oruga|Ardilla|Hormiga|Jirafa|León|Mariposa|Mariquita|Mono|Oso saludando|Oso sentado|Panda|Pelícano|Pollito|Insecto verde|Rana|Serpiente|Tortuga|Tigre|Cebra|Vaca|Loro|Dinosaurio|Unicornio|Cerdo|Paloma|Conejo')
group('CD', 'Niño con bastón y gafas')
group('CAR', 'Bienvenidos al año lectivo|Banderín de bienvenida|Bienvenidos al nuevo año lectivo|Bienvenida con nombre de profesora|Banderín con nombre de profesora')
names.update({'FY.CH.003': 'Sistema urinario', 'FY.CH.008': 'Esqueleto humano', 'FY.CH.009': 'Cerebro', 'FY.CH.010': 'Corazón humano'})
group('ER', 'Pareja con tocados de plumas|Pareja con pañuelo y falda|Pareja con sombreros|Pareja con pañuelos amarillos')
group('IM', 'Bajo eléctrico|Guitarra|Maracas|Saxofón|Tambor|Violín|Arpa')
group('ÑA', 'Niña con lápiz y manzana|Niña con libro azul|Niña con lápiz y cuaderno|Niña con vestido rosa|Niña sentada leyendo|Niña abrazando un lápiz|Niña escribiendo|Niña con delantal y manzana|Niña con brazos abiertos|Niña con libros')
group('ÑA', 'Niña con libro rojo|Niña con vestido y diadema|Niña graduada|Niña con cuaderno y lazo|Niña leyendo un libro rojo|Niña con cuerda de saltar|Niña con overol y lápiz', start=12)
group('ÑO', 'Niño con camiseta roja|Niño con libro amarillo|Niño con libro en la mano|Niño en patineta|Niño saludando|Niño con overol azul|Niño leyendo un libro verde|Niño con mochila|Niño graduado|Niño con balón de fútbol|Niño con lápiz')
group('OP', 'Bombero|Mecánico|Policía con uniforme verde|Enfermera con uniforme blanco|Enfermera con uniforme azul')
group('OP', 'Policía con radio|Cocinero|Carpintero', start=7)
group('PAQ', 'Paquete de útiles escolares|Paquete de estrellas|Paquete de los cinco sentidos|Paquete de corazones|Paquete de flores|Paquete de huellas y huesos')
group('PE', 'Pez azul y amarillo|Pez verde y rosa|Pez naranja y amarillo|Pez amarillo y verde|Pez azul|Pez naranja con franjas blancas')
group('PER', 'Oso con vaso|Criatura azul de orejas grandes|Erizo azul|Superhéroe con telarañas|Auto de carreras rojo|Perro con libro|Niño con traje rojo|Gatita con flor|Hada con vestido verde|Perro bombero con cartel|Perro policía con cartel|Perro constructor con cartel|Ratona con lazo rojo|Cara de perro policía|Cara de perro bombero|Cara de perro constructor')
group('RE', 'Sacerdote|Ángel con alas rosas|Ángel con alas azules|Hombre con túnica|Monja con rosario|Virgen con manto verde')
group('RE', 'Virgen con manto azul|Bebé en pesebre', start=8)
group('TOP', 'Topper Felicitaciones|Topper Feliz Día Mamá|Topper Feliz Cumple|Topper Feliz Día')
names.update({'FY.VAR.001': 'Mazo de juez', 'FY.VAR.002': 'Frasco con pastillas', 'FY.VAR.004': 'Volcán',
 'FY.VAR.005': 'Estetoscopio', 'FY.VAR.006': 'Planeta Tierra en una mano', 'FY.VAR.007': 'Esposas',
 'FY.VAR.009': 'Chaleco de policía', 'FY.VAR.010': 'Botiquín', 'FY.VAR.011': 'Bandera tricolor',
 'FY.VAR.012': 'Animal con cartel Feliz Día', 'FY.VAR.013': 'Iglesia', 'FY.VAR.014': 'Mapa del Ecuador',
 'FY.VAR.015': 'Casa', 'FY.VAR.017': 'Cerdo con órganos internos', 'FY.VAR.018': 'Anatomía interna del cerdo'})
pending = {'FY.VAR.019': 'Se ve un corte anatómico parcial, pero no se distinguen con suficiente certeza el animal ni el sistema representado. Se conserva el código.'}
assert set(names).issubset({r['code'] for r in rows})
review = []
for row in rows:
    old = row['name']
    new = names.get(row['code'], old)
    status = 'corrected' if old and old != new else 'named' if new and not old else 'retained' if new else 'pending'
    reason = pending.get(row['code'], 'Nombre descriptivo de la figura y sus elementos visibles; sin atribución de marca, etnia ni personaje.' if status == 'named' else 'Nombre previo compatible con la imagen.')
    if status == 'corrected':
        reason = 'El rótulo Endocrino contradice los riñones, uréteres y vejiga visibles. Se corrige a Sistema urinario.'
    review.append({'code': row['code'], 'old_name': old, 'name': new, 'status': status, 'reason': reason,
                   'image': row['image'], 'image_sha256': hashlib.sha256((ROOT/'app/static/img/products'/row['image']).read_bytes()).hexdigest()})
    row['name'] = new
with (ROOT/'data/catalog_seed.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
(ROOT/'data/catalog_names.json').write_text(json.dumps({r['code']: r['name'] for r in rows}, ensure_ascii=False, indent=2)+'\n')
(ROOT/'docs/name-review/review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2)+'\n')
with (ROOT/'docs/name-review/changes.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['code','old_name','name','status','reason']);writer.writeheader()
    writer.writerows({k:r[k] for k in writer.fieldnames} for r in review)
from collections import Counter
print(dict(Counter(r['status'] for r in review)))
