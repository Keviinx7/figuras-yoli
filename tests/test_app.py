import csv
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.extensions import db
from app.models import Category, Product, ProductImage
from app.services.search import normalize_search, search_products, public_products
from app.services.catalog_importer import import_catalog, seed_categories, FIELDS
from app.services.whatsapp import validate_cart, build_message, whatsapp_url, PHONES


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / 'instance')
        self.root = Path(self.temp.name)
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'test-only', 'SQLALCHEMY_DATABASE_URI': 'sqlite://',
                               'CATALOG_PDF': str(self.root / 'catalog.pdf')})
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        seed_categories()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()
        self.temp.cleanup()

    def product(self, code='FY.ÑA.001', name='Figura de prueba', active=True, category='Niñas'):
        product = Product(code=code, name=name, slug=code.lower().replace('.', '-'),
                          category=Category.query.filter_by(name=category).one(), is_active=active,
                          allows_customization=True)
        db.session.add(product)
        db.session.commit()
        return product

    def row(self, **kwargs):
        row = dict(zip(FIELDS, ['FY.ÑA.001', 'Prueba únicamente', 'Niñas', '', '', '', '1', '1']))
        row.update(kwargs)
        return row

    def import_rows(self, rows, reviewed=True):
        # Only a presence fixture; no fabricated PDF is placed under docs/.
        (self.root / 'catalog.pdf').write_bytes(b'%PDF-test-presence-fixture')
        path = self.root / 'seed.csv'
        with path.open('w', encoding='utf-8', newline='') as target:
            writer = csv.DictWriter(target, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return import_catalog(path, reviewed=reviewed)

    def line(self, **kwargs):
        line = {'product_code': 'FY.ÑA.001', 'quantity': 1, 'requested_size': '30 cm', 'personalization': 'Prueba'}
        line.update(kwargs)
        return line

    def token(self):
        self.client.get('/carrito')
        with self.client.session_transaction() as session:
            return session['csrf_token']

    def test_factory_and_main_routes(self):
        for route in ['/', '/catalogo', '/categorias', '/favoritos', '/carrito', '/contacto']:
            with self.subTest(route=route):
                result = self.client.get(route)
                self.assertEqual(result.status_code, 200)
                self.assertIn(b'Yoli', result.data)
        self.assertEqual(self.client.get('/desconocida').status_code, 404)

    def test_categories_idempotent_and_database_driven(self):
        seed_categories()
        self.assertEqual(Category.query.count(), 17)
        db.session.add(Category(name='Categoría de prueba', slug='prueba'))
        db.session.commit()
        self.assertIn('Categoría de prueba', self.client.get('/categorias').get_data(as_text=True))

    def test_product_model_relationships_and_dates(self):
        product = self.product()
        product.images.append(ProductImage(file_path='img/products/test.png', sort_order=1))
        db.session.commit()
        self.assertIsInstance(product.id, int)
        self.assertEqual(product.code, 'FY.ÑA.001')
        self.assertEqual(product.category.name, 'Niñas')
        self.assertIsNotNone(product.created_at)
        self.assertEqual(len(product.images), 1)

    def test_unique_code(self):
        self.product()
        with self.assertRaises(IntegrityError):
            self.product()
        db.session.rollback()

    def test_unique_slug(self):
        product = self.product()
        db.session.add(Product(code='FY.ÑA.002', slug=product.slug, category=product.category))
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_database_rejects_placeholder(self):
        with self.assertRaises(IntegrityError):
            self.product('FY.AN.000')
        db.session.rollback()

    def test_import_requires_pdf(self):
        result = import_catalog(self.root / 'missing.csv', reviewed=True)
        self.assertIn('Falta', result['errors'][0])
        self.assertEqual(Product.query.count(), 0)

    def test_import_requires_review(self):
        result = self.import_rows([self.row()], reviewed=False)
        self.assertTrue(result['errors'])
        self.assertEqual(Product.query.count(), 0)

    def test_import_idempotent_unicode_and_update(self):
        self.assertEqual(self.import_rows([self.row()])['created'], 1)
        result = self.import_rows([self.row(name='Nombre revisado')])
        self.assertEqual(result['updated'], 1)
        self.assertEqual(Product.query.count(), 1)
        self.assertEqual(Product.query.one().code, 'FY.ÑA.001')
        self.assertEqual(Product.query.one().name, 'Nombre revisado')

    def test_import_rejects_all_duplicate_rows(self):
        result = self.import_rows([self.row(), self.row()])
        self.assertEqual(result['omitted'], 2)
        self.assertEqual(Product.query.count(), 0)

    def test_import_rejects_placeholders(self):
        rows = [self.row(code=code) for code in ['FY.AN.000', 'FY.PER.000', 'FY.CAR.000', 'FY.TOP.000']]
        result = self.import_rows(rows)
        self.assertEqual(result['omitted'], 4)
        self.assertEqual(Product.query.count(), 0)

    def test_import_incomplete_category_and_flags(self):
        result = self.import_rows([self.row(category=''), self.row(code='FY.ÑA.002', is_active=''),
                                   self.row(code='FY.ÑA.003', category='Desconocida')])
        self.assertEqual(result['omitted'], 3)
        self.assertEqual(Product.query.count(), 0)

    def test_missing_optional_fields_are_not_invented(self):
        result = self.import_rows([self.row(name='', image='missing.webp')])
        self.assertEqual(result['created'], 1)
        self.assertGreaterEqual(len(result['warnings']), 2)
        self.assertIsNone(Product.query.one().name)
        self.assertEqual(Product.query.one().image_path, 'img/placeholder.svg')

    def test_image_traversal_rejected(self):
        result = self.import_rows([self.row(image='../../../../config.py')])
        self.assertEqual(result['omitted'], 1)

    def test_image_import_idempotent_preserves_gallery(self):
        original_static = self.app.static_folder
        self.app.static_folder = str(self.root / 'static')
        path = Path(self.app.static_folder) / 'img/products'
        path.mkdir(parents=True)
        (path / 'photo.png').write_bytes(b'test')
        self.import_rows([self.row(image='photo.png')])
        product = Product.query.one()
        product.images.append(ProductImage(file_path='img/products/other.png', sort_order=1))
        db.session.commit()
        self.import_rows([self.row(image='photo.png')])
        self.assertEqual(ProductImage.query.count(), 2)
        self.app.static_folder = original_static

    def test_normalization_preserves_enye(self):
        self.assertEqual(normalize_search('CARÁTULAS'), 'caratulas')
        self.assertEqual(normalize_search('FY.N\u0303A.001'), 'fy.ña.001')
        self.assertNotEqual(normalize_search('FY.ÑA.001'), normalize_search('FY.NA.001'))

    def test_search_name_code_category_and_literal_wildcards(self):
        self.product(name='Árbol educativo', category='Niñas')
        for term in ['ARBOL', 'fy.ña.001', 'NIÑAS']:
            self.assertEqual(search_products(public_products(), term).count(), 1)
        for term in ['FY.NA.001', 'ninas', '%', '_']:
            self.assertEqual(search_products(public_products(), term).count(), 0)

    def test_filters_and_pagination(self):
        for number in range(1, 14):
            self.product(code=f'FY.ÑA.{number:03d}', name=f'Prueba {number}')
        result = self.client.get('/catalogo?categoria=niñas&page=2')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'FY.', result.data)
        self.assertIn('13 productos', result.get_data(as_text=True))
        self.assertIn('0 productos', self.client.get('/catalogo?categoria=animales').get_data(as_text=True))

    def test_detail_and_lookup_use_codes(self):
        product = self.product()
        self.assertEqual(self.client.get('/producto/' + product.slug).status_code, 200)
        data = self.client.get('/api/productos?code=FY.ÑA.001').get_json()['products']
        self.assertEqual(data[0]['code'], 'FY.ÑA.001')
        self.assertNotIn('id', data[0])

    def test_inactive_products_and_categories_hidden(self):
        product = self.product(active=False)
        self.assertEqual(self.client.get('/producto/' + product.slug).status_code, 404)
        with self.assertRaises(ValueError):
            validate_cart([self.line()])
        product.is_active = True
        product.category.is_active = False
        db.session.commit()
        self.assertEqual(public_products().count(), 0)
        with self.assertRaises(ValueError):
            validate_cart([self.line()])

    def test_cart_validates_quantities_unknown_and_personalization(self):
        product = self.product()
        for quantity in [0, -1, 100, True, 1.5, '2']:
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                validate_cart([self.line(quantity=quantity)])
        with self.assertRaises(ValueError):
            validate_cart([self.line(product_code='FY.AN.999')])
        with self.assertRaises(ValueError):
            validate_cart([self.line(requested_size='x' * 121)])
        product.allows_customization = False
        db.session.commit()
        with self.assertRaises(ValueError):
            validate_cart([self.line()])

    def test_cart_rejects_invalid_shapes_and_limits(self):
        for lines in [[], {}, None, [1], [self.line()] * 51]:
            with self.subTest(lines=type(lines)), self.assertRaises(ValueError):
                validate_cart(lines)

    def test_personalizations_remain_separate(self):
        self.product()
        result = validate_cart([self.line(personalization='Uno'), self.line(personalization='Dos')])
        self.assertEqual(len(result), 2)
        self.assertNotEqual(result[0]['personalization'], result[1]['personalization'])

    def test_message_and_url_from_validated_data(self):
        self.product(name='Nombre verificado')
        line = self.line(name='Nombre manipulado')
        message = build_message(validate_cart([line]), 'Cliente', 'Tulcán', 'shipping')
        self.assertIn('Nombre verificado', message)
        self.assertNotIn('Nombre manipulado', message)
        self.assertIn('FY.ÑA.001', message)
        self.assertIn('tiempo de elaboración', message)
        self.assertNotIn('$0', message)
        parsed = urlsplit(whatsapp_url(PHONES[0], message))
        self.assertEqual(parse_qs(parsed.query)['text'][0], message)

    def test_message_rejects_unknown_delivery_and_contact(self):
        for name, city, delivery in [('', 'Tulcán', 'shipping'), ('A', '', 'shipping'), ('A', 'B', 'inventada')]:
            with self.assertRaises(ValueError):
                build_message([], name, city, delivery)
        with self.assertRaises(ValueError):
            whatsapp_url('1234', 'test')

    def test_csrf_required(self):
        self.assertEqual(self.client.post('/cotizacion', data={}).status_code, 400)

    def test_invalid_unicode_csrf_is_rejected(self):
        self.token()
        self.assertEqual(self.client.post('/cotizacion', data={'csrf_token': 'ñ'}).status_code, 400)

    def test_quote_revalidates_product_after_page_load(self):
        product = self.product()
        token = self.token()
        product.is_active = False
        db.session.commit()
        response = self.client.post('/cotizacion', data={'csrf_token': token, 'cart': json.dumps([self.line()]),
                                                        'name': 'Prueba', 'city': 'Tulcán', 'delivery': 'shipping'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('no está publicado', response.get_data(as_text=True))

    def test_long_quote_offers_copy_and_both_numbers(self):
        self.product()
        response = self.client.post('/cotizacion', data={'csrf_token': self.token(),
            'cart': json.dumps([self.line(personalization='a' * 500)] * 20),
            'name': 'Prueba', 'city': 'Tulcán', 'delivery': 'shipping'})
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Tu solicitud es extensa', html)
        for phone in PHONES:
            self.assertIn(f'href="https://wa.me/{phone}"', html)

    def test_import_malformed_headers_and_columns(self):
        (self.root / 'catalog.pdf').write_bytes(b'%PDF-test-presence-fixture')
        path = self.root / 'seed.csv'
        path.write_text('code,name\nFY.ÑA.001,Prueba\n')
        self.assertTrue(import_catalog(path, reviewed=True)['errors'])
        path.write_text(','.join(FIELDS) + '\nFY.ÑA.001,Prueba\n')
        self.assertEqual(import_catalog(path, reviewed=True)['omitted'], 1)

    def test_import_valid_rows_survive_invalid_rows(self):
        report = self.import_rows([self.row(), self.row(code='FY.ÑA.000')])
        self.assertEqual(report['created'], 1)
        self.assertEqual(report['omitted'], 1)
        self.assertEqual(Product.query.count(), 1)

    def test_quote_preview_escapes_and_does_not_store_customer(self):
        self.product()
        result = self.client.post('/cotizacion', data={'csrf_token': self.token(), 'cart': json.dumps([self.line()]),
                                                     'name': '<script>test</script>', 'city': 'Tulcán', 'delivery': 'shipping'})
        self.assertEqual(result.status_code, 200)
        self.assertNotIn(b'<script>test</script>', result.data)
        self.assertIn(b'&lt;script&gt;', result.data)
        self.assertEqual(result.headers['Cache-Control'], 'no-store')
        with self.client.session_transaction() as session:
            self.assertEqual(set(session), {'csrf_token'})

    def test_quote_invalid_cart_shows_error(self):
        response = self.client.post('/cotizacion', data={'csrf_token': self.token(), 'cart': '{'})
        self.assertEqual(response.status_code, 400)

    def test_cli_initialization_and_missing_pdf(self):
        runner = self.app.test_cli_runner()
        self.assertEqual(runner.invoke(args=['init-db']).exit_code, 0)
        result = runner.invoke(args=['import-catalog', 'data/catalog_seed.csv', '--reviewed'])
        self.assertEqual(result.exit_code, 1)
        self.assertIn('Falta', result.output)


if __name__ == '__main__':
    unittest.main()
