"""Isolated email regression and full HTTP flow. No Internet or local store writes."""
import hashlib
import logging
import re
from datetime import timedelta
from unittest.mock import patch
import test_customer_portal as portal_tests
from app import create_app, RedactAccountLinks
from app.extensions import db
from app.models.customer_email import AccountEmailToken, EmailRateLimit, OrderEmailOutbox
from app.models.customer_account import CustomerAccount, CustomerRequest
from app.models.commercial import Customer
from app.services.customer_portal import now
from app.services.account_email import issue_token, find_token, consume_token
from app.services.mail import send_mail, deliver_order_mail


class EmailTests(portal_tests.PortalTests):
    # Portal regressions also run with mail enabled, except their explicit default tests.
    def setUp(self):
        super().setUp()
        self.app.config.update(MAIL_ENABLED=True, MAIL_BACKEND='fake',
                               MAIL_FROM_ADDRESS='yoli@example.test',
                               PUBLIC_BASE_URL='https://tienda.example.test',
                               ORDER_EMAIL_NOTIFICATIONS_ENABLED=True)

    def enable_accounts(self):
        self.app.config.update(EMAIL_VERIFICATION_ENABLED=True, ACCOUNT_RECOVERY_ENABLED=True)

    def messages(self):
        return self.app.extensions['mail_outbox']

    def link(self, index=-1):
        return re.search(r'https://tienda.example.test(/\S+)', self.messages()[index].get_content()).group(1)

    def clear_limits(self):
        EmailRateLimit.query.delete()
        db.session.commit()

    def test_verification_lifecycle_and_reissue(self):
        self.enable_accounts()
        response, account = self.register()
        self.assertTrue(response.location.endswith('verificacion-pendiente'))
        self.assertFalse(account.email_verified)
        first = self.link()
        token = first.rsplit('/', 1)[1]
        stored = AccountEmailToken.query.one()
        self.assertEqual(stored.digest, hashlib.sha256(token.encode()).hexdigest())
        self.assertNotIn(token, str(stored.__dict__))
        self.assertEqual(self.client.get(first).status_code, 200)
        self.assertIsNone(stored.used_at)  # Email scanners cannot consume a GET.
        self.assertEqual(self.client.post(first).status_code, 400)  # CSRF
        self.assertEqual(self.post('/cuenta/reenviar-verificacion').status_code, 302)
        second = self.link()
        self.assertNotEqual(first, second)
        self.assertEqual(self.post(first).status_code, 400)
        self.assertEqual(self.post(second).status_code, 302)
        self.assertTrue(db.session.get(CustomerAccount, account.id).email_verified)
        self.assertEqual(self.post(second).status_code, 400)
        self.assertEqual(self.client.get('/cuenta/verificar/invalid').status_code, 400)
        self.post('/cuenta/reenviar-verificacion')
        self.post('/cuenta/reenviar-verificacion')
        self.assertEqual(self.post('/cuenta/reenviar-verificacion').status_code, 429)
        self.assertEqual(len(self.messages()), 2)

    def test_expiration_purpose_revocation_and_inactive(self):
        self.enable_accounts()
        _, account = self.register()
        for purpose in ('verify_email', 'reset_password'):
            token = issue_token(account, purpose)
            self.assertIsNone(find_token(token, 'verify_email' if purpose == 'reset_password' else 'reset_password'))
            row = find_token(token, purpose)
            row.expires_at = now() - timedelta(seconds=1)
            db.session.commit()
            self.assertIsNone(find_token(token, purpose))
            path = '/cuenta/verificar/' if purpose == 'verify_email' else '/cuenta/restablecer/'
            self.assertEqual(self.post(path + token).status_code, 400)
            token = issue_token(account, purpose)
            account.is_active = False
            db.session.commit()
            self.assertIsNone(find_token(token, purpose))
            account.is_active = True
            db.session.commit()
        token = issue_token(account, 'reset_password')
        account.set_password('otra-password-valida')
        db.session.commit()
        self.assertIsNone(find_token(token, 'reset_password'))

    def test_recovery_generic_rate_limit_and_disabled(self):
        self.enable_accounts()
        self.register()
        anon = self.app.test_client()
        existing = self.post('/cuenta/olvide-contrasena', {'email': 'cliente@example.com'}, client=anon)
        unknown = self.post('/cuenta/olvide-contrasena', {'email': 'unknown@example.com'}, client=anon)
        self.assertEqual(existing.data, unknown.data)
        self.assertEqual(len(self.messages()), 2)  # verification + reset
        for _ in range(4):
            self.post('/cuenta/olvide-contrasena', {'email': 'cliente@example.com'}, client=anon)
        self.assertEqual(self.post('/cuenta/olvide-contrasena', {'email': 'cliente@example.com'}, client=anon).status_code, 429)
        self.app.config['MAIL_ENABLED'] = False
        body = self.post('/cuenta/olvide-contrasena', {'email': 'new@example.com'}, client=anon).get_data(as_text=True)
        self.assertIn('no está disponible', body)
        self.assertNotIn('correo enviado', body.lower())
        self.assertEqual(send_mail('a@example.com', 'test', 'test'), 'disabled')

    def test_http_e2e_verification_order_status_and_recovery(self):
        self.enable_accounts()
        _, account = self.register()
        self.assertEqual(self.post(self.link()).status_code, 302)
        self.post('/cuenta/logout')
        self.assertEqual(self.login_client().status_code, 302)
        self.assertEqual(self.post('/cuenta/pedidos', self.cart_payload()).status_code, 302)
        order = CustomerRequest.query.one()
        self.assertEqual(len(self.messages()), 2)
        self.assertIsNotNone(OrderEmailOutbox.query.one().sent_at)
        admin = self.app.test_client()
        self.post('/login', dict(username='adminportal', password=self.staff_password), client=admin)
        self.post(f'/admin/pedidos/{order.id}/estado', {'status': 'processing'}, client=admin)
        self.assertEqual(len(self.messages()), 3)
        self.post(f'/admin/pedidos/{order.id}/estado', {'status': 'processing'}, client=admin)
        self.assertEqual(len(self.messages()), 3)
        self.assertIn('En elaboración', self.client.get(f'/cuenta/pedido/{order.id}').get_data(as_text=True))
        for message in self.messages()[1:]:
            body = message.get_content().lower()
            for forbidden in ('99999', '0.01', 'unit_price', 'cost', 'receta', 'material', 'margen', 'markup', 'ganancia', 'notas internas'):
                self.assertNotIn(forbidden, body)
            self.assertIn('según tamaño', body)
        anon = self.app.test_client()
        self.post('/cuenta/olvide-contrasena', {'email': account.email}, client=anon)
        path = self.link()
        self.assertEqual(anon.get(path).status_code, 200)
        self.assertEqual(anon.post(path, data={'password': 'clave-nueva-segura'}).status_code, 400)
        self.assertEqual(self.post(path, {'password': 'clave-nueva-segura', 'confirm': 'clave-nueva-segura'}, client=anon).status_code, 302)
        self.assertEqual(self.client.get('/cuenta').status_code, 302)  # prior session invalidated
        self.assertEqual(self.post(path, {'password': 'otra-clave-segura', 'confirm': 'otra-clave-segura'}, client=anon).status_code, 400)
        self.assertEqual(self.login_client(client=anon).status_code, 401)
        self.assertEqual(self.login_client(password='clave-nueva-segura', client=anon).status_code, 302)

    def test_email_change_uniqueness_no_customer_takeover(self):
        self.enable_accounts()
        _, account = self.register()
        old_link = self.link()
        self.post(old_link)
        customer_id = account.customer_id
        other = Customer(name='Internal customer', email='new@example.com', phone='0991234567')
        db.session.add(other)
        db.session.commit()
        payload = dict(name='Updated', phone='0991234567', email=' NEW@EXAMPLE.COM ', current_password='clave-segura-de-prueba')
        self.assertEqual(self.post('/cuenta/perfil', payload).status_code, 302)
        self.assertEqual(account.email, 'new@example.com')
        self.assertFalse(account.email_verified)
        self.assertEqual(account.customer_id, customer_id)
        self.assertNotEqual(account.customer_id, other.id)
        self.assertEqual(other.name, 'Internal customer')
        self.assertEqual(self.post(old_link).status_code, 400)
        self.assertEqual(self.post(self.link()).status_code, 302)
        second = self.app.test_client()
        self.register('taken@example.com', client=second)
        payload['email'] = 'taken@example.com'
        self.assertEqual(self.post('/cuenta/perfil', payload).status_code, 400)
        payload['email'] = 'different@example.com'
        payload['current_password'] = 'wrong'
        self.assertEqual(self.post('/cuenta/perfil', payload).status_code, 400)

    def test_smtp_failure_preserves_order_and_retries(self):
        self.register()
        self.app.config.update(MAIL_BACKEND='smtp', SMTP_HOST='smtp.example.test', SMTP_PORT=587)
        with patch('app.services.mail.smtplib.SMTP', side_effect=OSError('secret-password MUST NOT LOG')):
            with self.assertLogs(self.app.logger, level='WARNING') as logs:
                response = self.post('/cuenta/pedidos', self.cart_payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CustomerRequest.query.count(), 1)
        self.assertNotIn('secret-password', str(logs.output))
        row = OrderEmailOutbox.query.one()
        self.assertEqual(row.attempts, 1)
        self.assertIsNone(row.sent_at)
        self.app.config['MAIL_BACKEND'] = 'fake'
        deliver_order_mail(row.id)
        deliver_order_mail(row.id)
        self.assertEqual(len(self.messages()), 1)
        self.assertIsNotNone(row.sent_at)

    def test_host_poisoning_and_log_redaction(self):
        self.enable_accounts()
        page = self.client.get('/registro', base_url='http://evil.example').get_data(as_text=True)
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        response = self.client.post('/registro', data=dict(name='Host test', email='host@example.com', phone='0991234567',
            password='clave-segura-de-prueba', confirm='clave-segura-de-prueba', csrf_token=csrf),
            base_url='http://evil.example', headers={'Host': 'evil.example'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('https://tienda.example.test/', self.messages()[0].get_content())
        self.assertNotIn('evil.example', self.messages()[0].get_content())
        record = logging.LogRecord('werkzeug', 20, '', 0, 'GET /cuenta/restablecer/%s HTTP/1.1', ('sensitive',), None)
        RedactAccountLinks().filter(record)
        self.assertNotIn('sensitive', record.getMessage())

    def test_disabled_routes_and_inactive_recovery(self):
        _, account = self.register()
        token = issue_token(account, 'reset_password')
        self.assertEqual(self.client.get('/cuenta/restablecer/' + token).status_code, 404)
        self.enable_accounts()
        account.is_active = False
        db.session.commit()
        self.post('/cuenta/olvide-contrasena', {'email': account.email})
        self.assertEqual(len(self.messages()), 0)
        self.assertEqual(self.client.get('/cuenta').status_code, 302)

    def test_production_mail_config_validation(self):
        baseline = dict(TESTING=True, ENVIRONMENT='production', SECRET_KEY='a-valid-secret-of-at-least-32-characters',
                        SQLALCHEMY_DATABASE_URI='sqlite://', MAIL_ENABLED=True, MAIL_BACKEND='smtp',
                        SMTP_HOST='smtp.example.test', SMTP_PORT=587, SMTP_USE_TLS=True, SMTP_USE_SSL=False,
                        MAIL_FROM_ADDRESS='yoli@example.test', PUBLIC_BASE_URL='https://tienda.example.test',
                        EMAIL_VERIFICATION_ENABLED=True, ACCOUNT_RECOVERY_ENABLED=True)
        for invalid in ({'SMTP_HOST': ''}, {'SMTP_PORT': 0}, {'SMTP_USE_SSL': True},
                        {'PUBLIC_BASE_URL': 'http://evil.test'}, {'PUBLIC_BASE_URL': 'https://u:p@example.test'},
                        {'PUBLIC_BASE_URL': 'https://example.test/path'}, {'MAIL_ENABLED': False},
                        {'MAIL_BACKEND': 'fake'}, {'SMTP_PASSWORD': 'secret'}, {'SMTP_USE_TLS': False},
                        {'MAIL_FROM_NAME': 'Yoli\nBcc: other@example.test'}, {'ACCOUNT_RECOVERY_LIFETIME_HOURS': 0}):
            with self.subTest(invalid=list(invalid)), self.assertRaises(RuntimeError):
                create_app({**baseline, **invalid})
        app = create_app(baseline)
        self.assertEqual(app.config['MAIL_BACKEND'], 'smtp')

    def test_smtp_tls_ssl_transport_and_safe_failure_revocation(self):
        self.app.config.update(MAIL_BACKEND='smtp', SMTP_HOST='smtp.example.test', SMTP_PORT=587,
                               SMTP_USERNAME='test-user', SMTP_PASSWORD='test-password', SMTP_USE_TLS=True)
        with patch('app.services.mail.smtplib.SMTP') as smtp:
            self.assertEqual(send_mail('recipient@example.test', 'Subject', 'Body'), 'sent')
            connection = smtp.return_value.__enter__.return_value
            connection.starttls.assert_called_once()
            connection.login.assert_called_once_with('test-user', 'test-password')
            connection.send_message.assert_called_once()
            self.assertEqual(smtp.call_args.kwargs['timeout'], 10)
        self.app.config.update(SMTP_USE_TLS=False, SMTP_USE_SSL=True, SMTP_PORT=465)
        with patch('app.services.mail.smtplib.SMTP_SSL') as smtp:
            self.assertEqual(send_mail('recipient@example.test', 'Subject', 'Body'), 'sent')
            self.assertIn('context', smtp.call_args.kwargs)
        self.app.config.update(MAIL_BACKEND='fake', EMAIL_VERIFICATION_ENABLED=True)
        _, account = self.register()
        self.app.config.update(MAIL_BACKEND='smtp', ACCOUNT_RECOVERY_ENABLED=True)
        with patch('app.services.mail.smtplib.SMTP_SSL', side_effect=OSError('smtp-secret')):
            with self.assertLogs(self.app.logger, level='WARNING') as logs:
                self.post('/cuenta/olvide-contrasena', {'email': account.email})
        self.assertNotIn('smtp-secret', str(logs.output))
        self.assertEqual(AccountEmailToken.query.filter_by(purpose='reset_password', used_at=None).count(), 0)

    def test_token_atomic_consumption_and_rollback(self):
        _, account = self.register()
        token = issue_token(account, 'reset_password')
        self.assertIsNotNone(consume_token(token, 'reset_password'))
        self.assertIsNone(consume_token(token, 'reset_password'))
        db.session.rollback()
        self.assertIsNotNone(consume_token(token, 'reset_password'))
        db.session.commit()
        db.session.remove()
        self.assertIsNone(consume_token(token, 'reset_password'))

    def test_deactivation_revokes_links_even_after_reactivation(self):
        self.enable_accounts()
        _, account = self.register()
        verify_link = self.link()
        reset = issue_token(account, 'reset_password')
        admin = self.app.test_client()
        self.post('/login', dict(username='adminportal', password=self.staff_password), client=admin)
        for _ in range(2):
            self.post(f'/admin/pedidos/clientes/{account.customer_id}/cuenta', client=admin)
        self.assertTrue(account.is_active)
        self.assertIsNone(find_token(reset, 'reset_password'))
        self.assertEqual(self.post(verify_link).status_code, 400)

    def test_ip_throttle_unknown_accounts_and_disabled_notifications(self):
        self.app.config['ACCOUNT_RECOVERY_ENABLED'] = True
        for i in range(20):
            self.assertEqual(self.post('/cuenta/olvide-contrasena', {'email': f'unknown{i}@example.com'}).status_code, 200)
        self.assertEqual(self.post('/cuenta/olvide-contrasena', {'email': 'another@example.com'}).status_code, 429)
        self.register()
        self.app.config['ORDER_EMAIL_NOTIFICATIONS_ENABLED'] = False
        self.post('/cuenta/pedidos', self.cart_payload())
        self.assertEqual(CustomerRequest.query.count(), 1)
        self.assertEqual(OrderEmailOutbox.query.count(), 0)
        self.assertEqual(self.messages(), [])
        self.app.config.update(MAIL_BACKEND='disabled', ORDER_EMAIL_NOTIFICATIONS_ENABLED=True)
        self.post('/cuenta/pedidos', self.cart_payload())
        self.assertEqual(CustomerRequest.query.count(), 2)
        self.assertEqual(OrderEmailOutbox.query.count(), 0)
