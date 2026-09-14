"""Customer portal: registration, access, persisted requests and security.

Every request is isolated in a temporary SQLite database; nothing here
touches instance/tienda.db.
"""
import json
import secrets
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.extensions import db
from app.models import Product, Category
from app.models.commercial import User, Customer, LoginAttempt
from app.models.customer_account import (CustomerAccount, CustomerRequest,
                                         CustomerRequestItem, REQUEST_STATUS_LABELS)
from app.services.customer_portal import recovery_token, consume_recovery_token
from app.services.commercial import initialize_settings

ROOT = Path(__file__).resolve().parents[1]


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'instance')
        self.app = create_app({'TESTING': True, 'SECRET_KEY': secrets.token_hex(32),
                               'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + self.temp.name + '/portal.db',
                               'ACCOUNT_RECOVERY_ENABLED': False,
                               'EMAIL_VERIFICATION_ENABLED': False})
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        initialize_settings()
        self.staff_password = secrets.token_urlsafe(24)
        admin = User(username='adminportal', role='admin')
        admin.set_password(self.staff_password)
        seller = User(username='vendedorportal', role='vendedor')
        seller.set_password(self.staff_password)
        db.session.add_all([admin, seller])
        category = Category(name='Prueba', slug='prueba')
        db.session.add(category)
        db.session.flush()
        self.product = Product(code='FY.POR.001', name='Figura de prueba', slug='figura-prueba',
                               category_id=category.id, is_active=True, allows_customization=True)
        db.session.add(self.product)
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.engine.dispose()
        self.ctx.pop()
        self.temp.cleanup()

    def token(self, client=None):
        client = client or self.client
        with client.session_transaction() as session:
            return session.get('csrf_token')

    def post(self, path, data=None, client=None):
        client = client or self.client
        with client.session_transaction() as session:
            token = session.get('csrf_token')
        if not token:
            client.get('/')
            with client.session_transaction() as session:
                token = session.get('csrf_token')
        return client.post(path, data={**(data or {}), 'csrf_token': token})

    def register(self, email='cliente@example.com', password='clave-segura-de-prueba',
                 client=None, **extra):
        confirm = extra.pop('confirm', password)
        data = dict(name='Cliente Portal', email=email, phone='0991234567',
                    password=password, confirm=confirm, **extra)
        response = self.post('/registro', data, client=client)
        account = CustomerAccount.query.filter_by(email=email).first()
        return response, account

    def login_client(self, email='cliente@example.com', password='clave-segura-de-prueba',
                     client=None, **extra):
        return self.post('/cuenta/login', dict(email=email, password=password, **extra), client=client)

    def cart_payload(self):
        cart = [{'product_code': 'FY.POR.001', 'quantity': 2, 'requested_size': '20 cm',
                 'personalization': 'Nombre de prueba'},
                {'product_code': 'FY.POR.001', 'quantity': 1, 'requested_size': '30 cm',
                 'personalization': 'Otra variante'}]
        return dict(cart=json.dumps(cart), delivery='shipping', notes='Listo para coordinar',
                    total='99999', unit_price='0.01', subtotal='12345')

    def test_register_creates_customer_and_account_and_autologin(self):
        response, account = self.register()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].endswith('/cuenta'))
        customer = account.customer
        self.assertIsNotNone(customer)
        self.assertEqual(customer.name, 'Cliente Portal')
        self.assertEqual(customer.email, 'cliente@example.com')
        self.assertEqual(account.email, 'cliente@example.com')
        self.assertNotEqual(account.password_hash, 'clave-segura-de-prueba')
        self.assertTrue(account.password_hash.startswith('scrypt:'))
        self.assertFalse(account.email_verified)
        self.assertTrue(account.is_active)
        # El registro nunca crea un usuario del personal.
        self.assertEqual(User.query.count(), 2)
        self.assertEqual(self.client.get('/cuenta').status_code, 200)
        body = self.client.get('/cuenta').get_data(as_text=True)
        self.assertIn('Hola, Cliente Portal', body)

    def test_duplicate_email_rejected_without_new_account(self):
        self.register(email='dup@example.com')
        second = self.app.test_client()
        response, _ = self.register(email='dup@example.com', client=second)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Ya existe una cuenta', response.get_data(as_text=True))
        self.assertEqual(CustomerAccount.query.filter_by(email='dup@example.com').count(), 1)
        self.assertEqual(Customer.query.count(), 1)

    def test_weak_and_mismatched_passwords_rejected(self):
        for payload in [dict(password='corta'), dict(password='clave-segura-de-prueba', confirm='otra-clave-distinta')]:
            response, account = self.register(**payload)
            self.assertEqual(response.status_code, 400)
            self.assertIsNone(account)
        self.assertEqual(CustomerAccount.query.count(), 0)

    def test_login_success_and_generic_failure(self):
        self.register(email='entra@example.com')
        user = self.app.test_client()
        response = self.login_client('entra@example.com', client=user)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].endswith('/cuenta'))
        self.assertEqual(user.get('/cuenta').status_code, 200)
        self.assertEqual(CustomerAccount.query.filter_by(email='entra@example.com').one().is_active, True)

        wrong = self.login_client('entra@example.com', password='contrasena-1ncorrecta-x',
                                  client=self.app.test_client())
        self.assertEqual(wrong.status_code, 401)
        self.assertIn('Correo o contraseña incorrectos.', wrong.get_data(as_text=True))

    def test_login_missing_account_is_generic(self):
        response = self.login_client('no-existe@example.com', client=self.app.test_client())
        self.assertEqual(response.status_code, 401)
        self.assertIn('Correo o contraseña incorrectos.', response.get_data(as_text=True))

    def test_login_rate_limit_by_ip(self):
        client = self.app.test_client()
        for _ in range(10):
            self.assertEqual(self.login_client('cliente@example.com', password='contrasena-1ncorrecta-x',
                                               client=client).status_code, 401)
        self.assertEqual(self.login_client('cliente@example.com', password='contrasena-1ncorrecta-x',
                                           client=client).status_code, 429)

    def test_logout_ends_customer_session(self):
        self.register()
        self.assertEqual(self.client.get('/cuenta').status_code, 200)
        response = self.post('/cuenta/logout')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get('/cuenta').status_code, 302)
        with self.client.session_transaction() as session:
            self.assertNotIn('customer_account_id', session)

    def test_inactive_account_loses_session_and_login(self):
        _, account = self.register()
        self.assertEqual(self.client.get('/cuenta').status_code, 200)
        account.is_active = False
        db.session.commit()
        self.assertEqual(self.client.get('/cuenta').status_code, 302)
        with self.client.session_transaction() as session:
            session.clear()
        response = self.login_client(client=self.client)
        self.assertEqual(response.status_code, 401)

    def test_csrf_required_everywhere(self):
        self.assertEqual(self.client.post('/cuenta/login', data=dict(email='x@example.com', password='123456789012')).status_code, 400)
        self.assertEqual(self.client.post('/cuenta/pedidos', data=dict(cart='[]', delivery='shipping')).status_code, 400)
        self.assertEqual(self.client.post('/cuenta/logout').status_code, 400)
        self.register()
        self.assertEqual(self.client.post('/cuenta/pedidos', data=dict(cart='[]', delivery='shipping')).status_code, 400)

    def test_customer_never_reaches_admin(self):
        self.register()
        for path in ('/admin', '/admin/pedidos', '/admin/pedidos/1', '/admin/clientes', '/admin/pedidos/1/estado'):
            # 302 = blocked by login gate; 405 = method/route locked for the customer.
            self.assertIn(self.client.get(path).status_code, (302, 405))

    def test_admin_session_never_reaches_portal(self):
        self.post('/login', dict(username='adminportal', password=self.staff_password))
        with self.client.session_transaction() as session:
            self.assertIn('_user_id', session)
            self.assertNotIn('customer_account_id', session)
        self.assertEqual(self.client.get('/cuenta').status_code, 302)
        self.assertEqual(self.client.get('/cuenta/pedidos').status_code, 302)
        # Logging into the portal on the same browser replaces the staff session.
        self.register(email='mismo@example.com')
        with self.client.session_transaction() as session:
            self.assertIn('customer_account_id', session)
            self.assertNotIn('_user_id', session)
        self.assertEqual(self.client.get('/admin').status_code, 302)

    def test_sessions_rotate_and_cookie_is_safe(self):
        _, account = self.register()
        self.assertEqual(CustomerAccount.query.filter_by(email='cliente@example.com').one().session_token,
                         account.session_token)
        first_token = account.session_token
        # Logout keeps the token valid for the next login only after rotation.
        self.post('/cuenta/logout')
        self.login_client()
        fresh = db.session.get(CustomerAccount, account.id)
        self.assertNotEqual(fresh.session_token, first_token)
        with self.client.session_transaction() as session:
            self.assertEqual({k for k in session.keys()},
                             {'customer_account_id', 'customer_session_token', 'csrf_token', '_permanent'})
        # The session cookie is never readable from JavaScript.
        cookie = self.app.test_client().get('/registro').headers.get('Set-Cookie', '')
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=Lax', cookie)

    def test_next_is_local_only(self):
        self.register(email='next@example.com')
        bad = self.login_client('next@example.com', next='//evil.example.com/pagina', client=self.app.test_client())
        self.assertTrue(bad.headers['Location'].startswith('/cuenta'))
        good = self.login_client('next@example.com', next='/cuenta/pedidos', client=self.app.test_client())
        self.assertEqual(good.headers['Location'], '/cuenta/pedidos')

    def test_request_requires_login(self):
        anonymous = self.app.test_client()
        response = self.post('/cuenta/pedidos', self.cart_payload(), client=anonymous)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/cuenta/login', response.headers['Location'])
        self.assertEqual(CustomerRequest.query.count(), 0)
        self.assertEqual(anonymous.get('/cuenta/pedido/1').status_code, 302)

    def test_request_persists_without_prices_or_costs(self):
        self.register()
        response = self.post('/cuenta/pedidos', self.cart_payload())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].startswith('/cuenta/pedido/'))
        request_record = CustomerRequest.query.one()
        self.assertEqual(request_record.status, 'pending')
        self.assertEqual(len(request_record.items), 2)
        item = request_record.items[0]
        self.assertEqual(item.product_code_snapshot, 'FY.POR.001')
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.requested_size, '20 cm')
        self.assertEqual(item.personalization, 'Nombre de prueba')
        self.assertEqual(request_record.delivery, 'shipping')
        self.assertEqual(request_record.delivery_label, 'Envío (por confirmar)')
        # Los montos del formulario jamás se guardan.
        self.assertNotIn('99999', json.dumps(request_record.customer_snapshot))
        names = {column.name for column in CustomerRequest.__table__.columns}
        item_names = {column.name for column in CustomerRequestItem.__table__.columns}
        for forbidden in ('total', 'subtotal', 'tax', 'currency', 'unit_price',
                          'unit_cost', 'cost_snapshot'):
            self.assertNotIn(forbidden, names)
            self.assertNotIn(forbidden, item_names)
        body = self.client.get('/cuenta/pedido/%d' % request_record.id).get_data(as_text=True)
        self.assertIn('Lo que pediste', body)
        for forbidden in ('unit_price', 'unit_cost', 'cost_snapshot', 'margen',
                          'ganancia', 'costo de producción'):
            self.assertNotIn(forbidden, body.lower())
        self.assertIn(REQUEST_STATUS_LABELS['pending'], body)

    def test_invalid_cart_is_rejected_without_persistence(self):
        self.register()
        response = self.post('/cuenta/pedidos', dict(cart='[{"product_code":"NO.EXISTE","quantity":1}]',
                                                     delivery='shipping'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CustomerRequest.query.count(), 0)
        response = self.post('/cuenta/pedidos', dict(cart='esto-no-es-json', delivery='shipping'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CustomerRequest.query.count(), 0)

    def test_idor_hides_other_customers_requests(self):
        _, account_a = self.register(email='a@example.com')
        client_b = self.app.test_client()
        self.register(email='b@example.com', client=client_b)
        self.post('/cuenta/pedidos', dict(cart=json.dumps([{'product_code': 'FY.POR.001', 'quantity': 1}]),
                                          delivery='shipping'))
        request_record = CustomerRequest.query.one()
        self.assertEqual(request_record.account_id, account_a.id)
        # El otro cliente recibe 404, nunca la solicitud ajena.
        self.assertEqual(client_b.get('/cuenta/pedido/%d' % request_record.id).status_code, 404)
        self.assertEqual(self.client.get('/cuenta/pedido/%d' % request_record.id).status_code, 200)

    def test_profile_edit_and_readonly_email(self):
        self.register()
        response = self.post('/cuenta/perfil', dict(name='Nuevo Nombre', phone='0987654321',
                                                    address='Calle 1', city='Quito'))
        self.assertEqual(response.status_code, 302)
        customer = CustomerAccount.query.one().customer
        self.assertEqual(customer.name, 'Nuevo Nombre')
        self.assertEqual(customer.city, 'Quito')
        self.assertEqual(customer.email, 'cliente@example.com')

    def test_admin_staff_manages_requests_and_client_sees_status(self):
        self.register()
        self.post('/cuenta/pedidos', dict(cart=json.dumps([{'product_code': 'FY.POR.001', 'quantity': 1}]),
                                          delivery='shipping'))
        request_record = CustomerRequest.query.one()
        admin_client = self.app.test_client()
        self.post('/login', dict(username='adminportal', password=self.staff_password), client=admin_client)
        self.assertEqual(admin_client.get('/admin/pedidos').status_code, 200)
        self.assertIn('FY.POR.001', admin_client.get('/admin/pedidos/%d' % request_record.id).get_data(as_text=True))
        response = self.post('/admin/pedidos/%d/estado' % request_record.id, dict(status='processing'),
                             client=admin_client)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(db.session.get(CustomerRequest, request_record.id).status, 'processing')
        # Estado inválido rechazado.
        response = self.post('/admin/pedidos/%d/estado' % request_record.id, dict(status='perdido'),
                             client=admin_client)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(db.session.get(CustomerRequest, request_record.id).status, 'processing')
        response = self.post('/admin/pedidos/%d/estado' % request_record.id, dict(status='completed'),
                             client=admin_client)
        self.assertEqual(response.status_code, 302)
        body = self.client.get('/cuenta/pedido/%d' % request_record.id).get_data(as_text=True)
        self.assertIn(REQUEST_STATUS_LABELS['completed'], body)

    def test_vendedor_manages_requests_but_not_accounts(self):
        self.register()
        customer = CustomerAccount.query.one().customer
        seller = self.app.test_client()
        self.post('/login', dict(username='vendedorportal', password=self.staff_password), client=seller)
        self.assertEqual(seller.get('/admin/pedidos').status_code, 200)
        response = self.post('/admin/pedidos/clientes/%d/cuenta' % customer.id,
                             dict(action='deactivate'), client=seller)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(db.session.get(CustomerAccount, CustomerAccount.query.one().id).is_active)

    def test_admin_toggle_account_never_touches_password(self):
        self.register()
        account = CustomerAccount.query.one()
        customer = account.customer
        admin_client = self.app.test_client()
        self.post('/login', dict(username='adminportal', password=self.staff_password), client=admin_client)
        original_hash = account.password_hash
        response = self.post('/admin/pedidos/clientes/%d/cuenta' % customer.id,
                             dict(action='deactivate', password='intento-de-cambio'), client=admin_client)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(db.session.get(CustomerAccount, account.id).is_active)
        self.assertEqual(db.session.get(CustomerAccount, account.id).password_hash, original_hash)
        response = self.post('/admin/pedidos/clientes/%d/cuenta' % customer.id,
                             dict(action='activate', password='otro-intento'), client=admin_client)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(db.session.get(CustomerAccount, account.id).is_active)
        self.assertEqual(db.session.get(CustomerAccount, account.id).password_hash, original_hash)

    def test_recover_is_honest_and_tokens_are_secure(self):
        self.register(email='olvido@example.com')
        body = self.client.get('/cuenta/recuperar').get_data(as_text=True)
        self.assertIn('no está activa', body)
        self.assertIn('WhatsApp', body)
        # Pedir recuperación no cambia contraseña ni finge envío.
        response = self.post('/cuenta/recuperar', dict(email='olvido@example.com'))
        self.assertEqual(response.status_code, 200)
        account = CustomerAccount.query.filter_by(email='olvido@example.com').one()
        original_hash = account.password_hash
        self.app.config['ACCOUNT_RECOVERY_ENABLED'] = True
        token = recovery_token(account)
        self.assertIsNotNone(consume_recovery_token(token))
        self.assertIsNone(consume_recovery_token(token + 'corrompido'))
        # Restablecer rota la contraseña y mata el token.
        reset_client = self.app.test_client()
        response = self.post('/cuenta/recuperar/%s' % token,
                             dict(password='nueva-clave-segura-123', confirm='nueva-clave-segura-123'),
                             client=reset_client)
        self.assertEqual(response.status_code, 302)
        fresh = db.session.get(CustomerAccount, account.id)
        self.assertTrue(fresh.check_password('nueva-clave-segura-123'))
        self.assertNotEqual(fresh.password_hash, original_hash)
        self.assertIsNone(consume_recovery_token(token))
        # Un enlace viejo jamás reabre la cuenta.
        second = self.app.test_client()
        self.register(email='olvido2@example.com', client=second)
        second_account = CustomerAccount.query.filter_by(email='olvido2@example.com').one()
        stale = recovery_token(second_account)
        second_account.set_password('otra-clave-segura-456')
        db.session.commit()
        self.assertIsNone(consume_recovery_token(stale))
        # Token para enlace inválido no permite restablecer.
        response = reset_client.get('/cuenta/recuperar/zzzz')
        self.assertEqual(response.status_code, 400)

    def test_config_flags_default_off(self):
        self.assertFalse(self.app.config['ACCOUNT_RECOVERY_ENABLED'])
        self.assertFalse(self.app.config['EMAIL_VERIFICATION_ENABLED'])
        self.assertEqual(self.app.config['ACCOUNT_RECOVERY_LIFETIME_HOURS'], 1)


if __name__ == '__main__':
    unittest.main()