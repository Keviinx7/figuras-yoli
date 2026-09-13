import csv
import re
from pathlib import Path
import click
from flask import current_app
from flask.cli import with_appcontext
from app.extensions import db
from app.models import Category, Product, ProductImage
from app.services.search import normalize_search

CATEGORIES = ['Animales', 'Capacidades diferentes', 'Carteles', 'Cuerpo humano y células',
              'Etnias y regiones', 'Instrumentos musicales', 'Navideños', 'Niñas', 'Niños',
              'Oficios y profesiones', 'Paquetes', 'Peces', 'Personajes', 'Religiosos',
              'Toppers', 'Varios', 'Carátulas']
FIELDS = ['code', 'name', 'category', 'image', 'description', 'size_notes', 'allows_customization', 'is_active']
CODE_PATTERN = re.compile(r'^FY\.[A-ZÑ]+\.[0-9]{3}$')


def seed_categories():
    for order, name in enumerate(CATEGORIES):
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name, slug=normalize_search(name).replace(' ', '-'), sort_order=order))
    db.session.commit()


def import_catalog(path, reviewed=False):
    report = {'created': 0, 'updated': 0, 'omitted': 0, 'errors': [], 'warnings': []}
    if not Path(current_app.config['CATALOG_PDF']).is_file():
        report['errors'].append('Falta docs/catalogo-productos.pdf. Importación detenida.')
        return report
    if not reviewed:
        report['errors'].append('Revise el PDF y verifique el CSV antes de usar --reviewed.')
        return report
    try:
        with Path(path).open(encoding='utf-8-sig', newline='') as source:
            reader = csv.DictReader(source)
            if reader.fieldnames != FIELDS:
                report['errors'].append('Encabezados CSV inválidos. Se esperan: ' + ', '.join(FIELDS))
                return report
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        report['errors'].append(f'No se pudo leer el CSV: {exc}')
        return report
    counts = {}
    for row in rows:
        code = (row.get('code') or '').strip()
        counts[code] = counts.get(code, 0) + 1
    for number, row in enumerate(rows, 2):
        errors = []
        if None in row or any(value is None for value in row.values()):
            report['errors'].append(f'Fila {number}: número de columnas incorrecto.')
            report['omitted'] += 1
            continue
        row = {key: value.strip() for key, value in row.items()}
        code = row['code']
        if not CODE_PATTERN.fullmatch(code):
            errors.append('código inválido (formato FY.PREFIJO.001)')
        if code.endswith('000'):
            errors.append('código placeholder 000 excluido')
        if counts[code] > 1:
            errors.append('código duplicado dentro del CSV')
        category = Category.query.filter_by(name=row['category']).first()
        if not category:
            errors.append('categoría desconocida o vacía')
        for key in ('allows_customization', 'is_active'):
            if row[key] not in ('0', '1'):
                errors.append(f'{key} debe ser 0 o 1; no se infiere un valor')
        image = row['image']
        if image:
            root = (Path(current_app.static_folder) / 'img/products').resolve()
            candidate = (root / image).resolve()
            if not candidate.is_relative_to(root) or candidate.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp'):
                errors.append('ruta o formato de imagen no permitido')
            elif not candidate.is_file():
                report['warnings'].append(f'Fila {number}: imagen faltante; se usará placeholder.')
                image = ''
        else:
            report['warnings'].append(f'Fila {number}: sin imagen; se usará placeholder.')
        if not row['name']:
            report['warnings'].append(f'Fila {number}: nombre pendiente; se mostrará el código.')
        if errors:
            report['omitted'] += 1
            report['errors'].append(f'Fila {number} ({code or "sin código"}): ' + '; '.join(errors))
            continue
        product = Product.query.filter_by(code=code).first()
        if product is None:
            product = Product(code=code, slug=code.lower().replace('.', '-'))
            db.session.add(product)
            report['created'] += 1
        else:
            report['updated'] += 1
        for key in ('name', 'description', 'size_notes'):
            setattr(product, key, row[key] or None)
        product.category = category
        product.allows_customization = row['allows_customization'] == '1'
        product.is_active = row['is_active'] == '1'
        # CSV owns the primary image only; extra gallery images are preserved.
        primary = next((item for item in product.images if item.sort_order == 0), None)
        if image:
            if primary is None:
                primary = ProductImage(sort_order=0)
                product.images.append(primary)
            primary.file_path = 'img/products/' + image
            primary.alt_text = product.display_name
        elif primary:
            db.session.delete(primary)
    db.session.commit()
    return report


@click.command('import-catalog')
@click.argument('path', type=click.Path(exists=True), default='data/catalog_seed.csv')
@click.option('--reviewed', is_flag=True, help='Confirma que el PDF fue revisado y el CSV verificado.')
@with_appcontext
def import_command(path, reviewed):
    report = import_catalog(path, reviewed)
    for key, value in report.items():
        click.echo(f'{key}: {value}')
    if report['errors']:
        raise click.ClickException('Importación terminada con errores; revise los registros omitidos.')
