"""Reproduce the extraction after the visual review documented in docs/catalog-audit/.
Requires Poppler and ImageMagick; no OCR, generated images or inferred product codes.
"""
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'docs/catalogo-productos.pdf'
REVIEWED_SHA256 = '52d58526c7c3ae074abe0cb6a8fe9656da0780e7b6c3cdaafbb52b2a1c7766bc'
AUDIT = ROOT / 'docs/catalog-audit'
IMAGES = ROOT / 'app/static/img/products'
CATEGORIES = dict(zip(
    ['AN', 'CD', 'CAR', 'CH', 'ER', 'IM', 'NAV', 'ÑA', 'ÑO', 'OP', 'PAQ', 'PE', 'PER', 'RE', 'TOP', 'VAR'],
    ['Animales', 'Capacidades diferentes', 'Carteles', 'Cuerpo humano y células', 'Etnias y regiones',
     'Instrumentos musicales', 'Navideños', 'Niñas', 'Niños', 'Oficios y profesiones', 'Paquetes',
     'Peces', 'Personajes', 'Religiosos', 'Toppers', 'Varios']))
# Only labels actually printed beside/on the product, transcribed after visual review.
NAMES = {
    'FY.CH.001': 'Digestivo', 'FY.CH.002': 'Circulatorio', 'FY.CH.003': 'Endocrino',
    'FY.CH.004': 'Nervioso', 'FY.CH.005': 'Respiratorio', 'FY.CH.006': 'Reproductor femenino',
    'FY.CH.007': 'Reproductor masculino', 'FY.CH.011': 'Célula animal',
    'FY.CH.012': 'Célula procariota', 'FY.CH.013': 'Célula vegetal',
    'FY.NAV.001': 'Melchor', 'FY.NAV.002': 'Baltazar', 'FY.NAV.003': 'Gaspar',
    'FY.NAV.004': 'Bota navideña', 'FY.NAV.005': 'Reno navideño', 'FY.NAV.006': 'Muñeco de nieve',
    'FY.OP.006': 'Maestra', 'FY.RE.007': 'Virgen de la Medalla Milagrosa',
    'FY.RE.010': 'María', 'FY.RE.011': 'José', 'FY.VAR.003': 'Identificativos',
    'FY.VAR.008': 'Ciclo del agua', 'FY.VAR.016': 'Identificativos',
}
FIELDS = ['code', 'name', 'category', 'image', 'description', 'size_notes', 'allows_customization', 'is_active']


def run(*args):
    subprocess.run(args, check=True, cwd=ROOT)


def main():
    assert hashlib.sha256(PDF.read_bytes()).hexdigest() == REVIEWED_SHA256, 'PDF changed: visual review required'
    AUDIT.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)
    run('pdftotext', '-layout', str(PDF), str(AUDIT / 'text.txt'))
    pages = (AUDIT / 'text.txt').read_text().split('\f')
    assert len(pages) == 34 and not pages[-1].strip(), 'Expected exactly 33 pages'
    # Preserve the subsequent visual naming review when reproducing this PDF.
    name_file = ROOT / 'data/catalog_names.json'
    reviewed_names = json.loads(name_file.read_text()) if name_file.exists() else {}
    rows, evidence, page_reports = [], [], []
    seen = set()
    for number, page in enumerate(pages[:-1], 1):
        raw_codes = re.findall(r'FY\.[A-ZÑ]+\.\s*\d{3}', page)
        assert len(raw_codes) == (0 if number in (1, 29, 30) else 9)
        report = {'page': number, 'real_coded': 0, 'uncoded': 9 if number == 29 else 0,
                  'placeholders_000': 0, 'logo_nonzero': 0}
        render = AUDIT / f'source-{number:02d}.png'
        if 2 <= number <= 29:
            run('pdftoppm', '-f', str(number), '-l', str(number), '-singlefile', '-scale-to', '2400',
                '-png', str(PDF), str(render.with_suffix('')))
            dimensions = subprocess.check_output(['magick', 'identify', '-format', '%w %h', str(render)], text=True)
            width, height = map(int, dimensions.split())
        for slot, raw in enumerate(raw_codes if number != 29 else [''] * 9):
            code = re.sub(r'\s+', '', raw)
            item = {'page': number, 'slot': slot + 1, 'printed_code': raw, 'code': code}
            if code.endswith('.000'):
                report['placeholders_000'] += 1
                item['status'] = 'excluded_000'
            elif number >= 31:
                report['logo_nonzero'] += 1
                item['status'] = 'excluded_logo_template'
            else:
                row, col = divmod(slot, 3)
                # Reviewed 3x3 cells, including their printed identifier. Coordinates
                # are fractions of the full page; no product synthesis or retouching.
                xs, ys = [0, 140, 267, 400], [95, 222, 349, 477]
                if code == 'FY.VAR.003':
                    xs[2] = 258  # Wider source frame: retain the left bear.
                x0, x1 = [round(xs[c] / 400 * width) for c in (col, col + 1)]
                y0, y1 = [round(ys[r] / 566 * height) for r in (row, row + 1)]
                filename = f'{code}.png' if code else f'uncoded-page-29-slot-{slot + 1:02d}.png'
                run('magick', str(render), '-crop', f'{x1-x0}x{y1-y0}+{x0}+{y0}', '+repage', str(IMAGES / filename))
                item.update(image=filename, crop_pixels=[x0, y0, x1, y1], source_pixels=[width, height],
                            image_sha256=hashlib.sha256((IMAGES / filename).read_bytes()).hexdigest())
                if code:
                    assert code not in seen, f'Duplicate real code: {code}'
                    seen.add(code)
                    report['real_coded'] += 1
                    item['status'] = 'importable'
                    category = CATEGORIES[code.split('.')[1]]
                    rows.append(dict(zip(FIELDS, [code, reviewed_names.get(code, NAMES.get(code, '')), category, filename, '', '', '1', '1'])))
                else:
                    item['status'] = 'pending_code'
                    item['category'] = 'Carátulas'
            evidence.append(item)
        page_reports.append(report)
    with (ROOT / 'data/catalog_seed.csv').open('w', encoding='utf-8', newline='') as target:
        writer = csv.DictWriter(target, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    result = {'pdf_sha256': hashlib.sha256(PDF.read_bytes()).hexdigest(), 'pages': page_reports,
              'totals': {'importable': len(rows), 'uncoded': 9,
                         'placeholders_000': sum(p['placeholders_000'] for p in page_reports),
                         'logo_nonzero': sum(p['logo_nonzero'] for p in page_reports),
                         'images': len(rows) + 9, 'missing_images': 0, 'unnamed': sum(not r['name'] for r in rows)},
              'categories': dict(Counter(r['category'] for r in rows)), 'items': evidence}
    (AUDIT / 'manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result['totals'], ensure_ascii=False))


if __name__ == '__main__':
    main()
