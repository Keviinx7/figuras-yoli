"""Apply reviewed names only. Run from the root: python -m scripts.update_catalog_names."""
import csv
import json
import sqlite3
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models import Product, ProductImage

ROOT = Path(__file__).resolve().parents[1]


def apply_names(rows, review):
    codes = [r['code'] for r in rows]
    products = {p.code: p for p in Product.query.all()}
    evidence = {r['code']: r for r in review}
    if len(codes) != len(set(codes)) or set(codes) != set(products) or set(codes) != set(evidence):
        raise ValueError('CSV, revisión y SQLite deben contener exactamente los mismos códigos únicos.')
    for row in rows:
        item = evidence[row['code']]
        if row['name'] != item['name'] or (products[row['code']].name or '') not in (item['old_name'], item['name']):
            raise ValueError('Nombre sin revisión o modificado externamente: ' + row['code'])
    changed = []
    for row in rows:
        product = products[row['code']]
        if (product.name or '') == row['name']:
            continue
        changed.append(product.code)
        product.name = row['name'] or None
        # Update existing alt text only; image IDs, paths and order are preserved.
        for image in product.images:
            if image.alt_text in (None, '', product.code, evidence[product.code]['old_name']):
                image.alt_text = product.display_name
    db.session.flush()
    return changed


def main():
    rows = list(csv.DictReader((ROOT/'data/catalog_seed.csv').open()))
    review = json.loads((ROOT/'docs/name-review/review.json').read_text())
    with create_app().app_context():
        before = [(p.id,p.code,p.slug,p.category_id,p.is_active,p.allows_customization,p.is_featured,p.description,p.size_notes) for p in Product.query.order_by(Product.id)]
        images = [(p.id,p.product_id,p.file_path,p.sort_order) for p in ProductImage.query.order_by(ProductImage.id)]
        backup = ROOT/'docs/name-review/tienda-before-names.db'
        if not backup.exists():
            with sqlite3.connect(db.engine.url.database) as source, sqlite3.connect(backup) as target:
                source.backup(target)
        try:
            changed = apply_names(rows, review)
            after = [(p.id,p.code,p.slug,p.category_id,p.is_active,p.allows_customization,p.is_featured,p.description,p.size_notes) for p in Product.query.order_by(Product.id)]
            assert before == after, 'Only names may change'
            assert images == [(p.id,p.product_id,p.file_path,p.sort_order) for p in ProductImage.query.order_by(ProductImage.id)]
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        result = {'reviewed': len(rows), 'changed': len(changed), 'codes': changed, 'products': Product.query.count(),
                  'images': ProductImage.query.count(), 'integrity': db.session.execute(db.text('PRAGMA integrity_check')).scalar()}
        (ROOT/'docs/name-review/database-update.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print({k:v for k,v in result.items() if k != 'codes'})


if __name__ == '__main__':
    main()
