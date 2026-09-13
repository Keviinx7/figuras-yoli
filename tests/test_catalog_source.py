"""Integration checks against the reviewed PDF extraction, using isolated SQLite."""
import csv
import hashlib
import json
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from app import create_app
from app.extensions import db
from app.models import Category, Product, ProductImage
from app.services.catalog_importer import import_catalog, seed_categories

ROOT = Path(__file__).resolve().parents[1]


class ReviewedCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / 'docs/catalog-audit/manifest.json').read_text())
        with (ROOT / 'data/catalog_seed.csv').open(newline='') as source:
            cls.rows = list(csv.DictReader(source))
        cls.app = create_app({'TESTING': True, 'SECRET_KEY': 'catalog-test', 'SQLALCHEMY_DATABASE_URI': 'sqlite://'})
        cls.context = cls.app.app_context()
        cls.context.push()
        db.create_all()
        seed_categories()
        cls.report = import_catalog(ROOT / 'data/catalog_seed.csv', reviewed=True)
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        cls.context.pop()

    def test_source_and_image_provenance(self):
        self.assertEqual(hashlib.sha256((ROOT / 'docs/catalogo-productos.pdf').read_bytes()).hexdigest(), self.manifest['pdf_sha256'])
        self.assertEqual(len(self.manifest['pages']), 33)
        images = [item for item in self.manifest['items'] if 'image' in item]
        self.assertEqual(len(images), 182)
        for item in images:
            with self.subTest(page=item['page'], slot=item['slot']):
                path = ROOT / 'app/static/img/products' / item['image']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item['image_sha256'])
                self.assertEqual(path.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')

    def test_real_codes_exclusions_and_unknown_fields(self):
        self.assertEqual(self.report['created'], 173)
        self.assertEqual(self.report['errors'], [])
        self.assertEqual(Product.query.count(), 173)
        self.assertEqual(ProductImage.query.count(), 173)
        imported = {row['code'] for row in self.rows}
        source = {item['code'] for item in self.manifest['items'] if item['status'] == 'importable'}
        self.assertEqual(imported, source)
        self.assertEqual(len(imported), len(self.rows))
        self.assertFalse(any(code.endswith('.000') for code in imported))
        self.assertNotIn('FY.ÑA.011', imported)
        self.assertIn('FY.ÑA.012', imported)
        self.assertIn('FY.ÑO.011', imported)
        self.assertEqual(sum(i['status'] == 'excluded_000' for i in self.manifest['items']), 77)
        self.assertEqual(sum(i['status'] == 'excluded_logo_template' for i in self.manifest['items']), 20)
        self.assertEqual(sum(i['status'] == 'pending_code' for i in self.manifest['items']), 9)
        self.assertTrue(all(not row['size_notes'] for row in self.rows))

    def test_every_real_detail_search_and_image(self):
        for product in Product.query.all():
            with self.subTest(code=product.code):
                result = self.client.get('/catalogo', query_string={'q': product.code})
                self.assertEqual(result.status_code, 200)
                self.assertIn('1 productos', result.get_data(as_text=True))
                self.assertIn(product.code, result.get_data(as_text=True))
                self.assertEqual(self.client.get('/producto/' + product.slug).status_code, 200)
                response = self.client.get('/static/' + product.image_path)
                self.assertEqual(response.status_code, 200)
                response.close()
        self.assertIn('0 productos', self.client.get('/catalogo?q=FY.NA.012').get_data(as_text=True))
        self.assertIn('1 productos', self.client.get('/catalogo?q=CELULA%20VEGETAL').get_data(as_text=True))

    def test_all_categories_and_pagination(self):
        self.assertEqual(Category.query.count(), 17)
        for category in Category.query.all():
            count = self.manifest['categories'].get(category.name, 0)
            with self.subTest(category=category.name):
                result = self.client.get('/catalogo', query_string={'categoria': category.slug})
                self.assertEqual(result.status_code, 200)
                self.assertIn(f'{count} productos', result.get_data(as_text=True))
        for page in range(1, 16):
            html = self.client.get('/catalogo', query_string={'page': page}).get_data(as_text=True)
            self.assertEqual(html.count('<article class="product-card">'), 12 if page < 15 else 5)

    def test_real_unicode_cart_lookup_and_whatsapp(self):
        codes = ['FY.ÑA.012', 'FY.ÑO.011']
        data = self.client.get('/api/productos', query_string={'code': codes}).get_json()
        self.assertEqual({item['code'] for item in data['products']}, set(codes))
        for route in ['/', '/favoritos', '/carrito', '/categorias', '/contacto']:
            self.assertEqual(self.client.get(route).status_code, 200)
        with self.client.session_transaction() as session:
            token = session['csrf_token']
        response = self.client.post('/cotizacion', data={'csrf_token': token, 'name': 'Verificación',
            'city': 'Tulcán', 'delivery': 'shipping', 'cart': json.dumps([
                {'product_code': code, 'quantity': 2, 'requested_size': '', 'personalization': 'Nombre de prueba'} for code in codes])})
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        from html import unescape
        import re
        links = re.findall(r'href="(https://wa.me/[^\"]+)"', html)
        links = [link for link in links if 'FY.' in link]
        self.assertEqual(len(links), 2)
        for link in links:
            parsed = urlsplit(unescape(link))
            self.assertIn(parsed.path, ['/593969080116', '/593986791895'])
            message = parse_qs(parsed.query)['text'][0]
            for code in codes:
                self.assertIn(code, message)
            self.assertNotIn('$0', message)

    def test_reimport_keeps_counts(self):
        report = import_catalog(ROOT / 'data/catalog_seed.csv', reviewed=True)
        self.assertEqual((report['created'], report['updated'], report['omitted']), (0, 173, 0))
        self.assertEqual(ProductImage.query.count(), 173)

    def test_reviewed_names_search_and_separate_codes(self):
        from app.services.search import public_products, search_products
        review = json.loads((ROOT/'docs/name-review/review.json').read_text())
        expected = json.loads((ROOT/'data/catalog_names.json').read_text())
        self.assertEqual(len(review), 173)
        self.assertEqual(sum(r['status'] == 'named' for r in review), 149)
        self.assertEqual(sum(r['status'] == 'corrected' for r in review), 1)
        self.assertEqual({r['code'] for r in review if r['status'] == 'pending'}, {'FY.VAR.019'})
        for product in Product.query.all():
            with self.subTest(code=product.code):
                self.assertEqual(product.name or '', expected[product.code])
                if product.name:
                    self.assertIn(product.code, {p.code for p in search_products(public_products(), product.name).all()})
        for term in ['Gato', 'FY.AN.001']:
            html = self.client.get('/catalogo', query_string={'q': term}).get_data(as_text=True)
            self.assertIn('>Gato</a>', html)
            self.assertIn('Código: FY.AN.001', html)
        self.assertEqual(Product.query.filter_by(code='FY.CH.003').one().name, 'Sistema urinario')
        self.assertEqual(Product.query.filter_by(code='FY.ÑA.012').one().name, 'Niña con libro rojo')
        self.assertEqual(Product.query.filter_by(code='FY.NA.012').count(), 0)
        with (ROOT/'docs/name-review/before.csv').open() as source:
            before = {row['code']: row for row in csv.DictReader(source)}
        for row in self.rows:
            self.assertEqual({k:v for k,v in row.items() if k != 'name'}, {k:v for k,v in before[row['code']].items() if k != 'name'})

    def test_names_only_update_is_idempotent_and_rejects_partial_catalog(self):
        from scripts.update_catalog_names import apply_names
        review = json.loads((ROOT/'docs/name-review/review.json').read_text())
        product = Product.query.filter_by(code='FY.AN.001').one()
        original = (product.id, product.slug, product.category_id, product.image_path)
        product.name = None
        db.session.flush()
        self.assertEqual(apply_names(self.rows, review), ['FY.AN.001'])
        self.assertEqual(apply_names(self.rows, review), [])
        self.assertEqual((product.id, product.slug, product.category_id, product.image_path), original)
        with self.assertRaises(ValueError):
            apply_names(self.rows[:-1], review)
        self.assertEqual(Product.query.count(), 173)
        self.assertEqual(ProductImage.query.count(), 173)

    def test_home_shows_existing_catalog_without_featured_flags(self):
        html = self.client.get('/').get_data(as_text=True)
        self.assertNotIn('Estamos preparando nuestro catálogo', html)
        self.assertEqual(html.count('<article class="product-card">'), 8)
        self.assertIn('>Gato</a>', html)
        self.assertEqual(Product.query.filter_by(is_featured=True).count(), 0)
