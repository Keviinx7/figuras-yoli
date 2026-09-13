"""Pruebas de la configuración por entorno, seguridad web y páginas de error.

Isola el entorno real del proceso: se restaura tras cada test. Las apps usan
bases SQLite temporales dentro de instance/ (nunca tienda.db).
"""
import os
import secrets
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.extensions import db
from config import get_config, valid_secret, ROOT

ENV_KEYS = ('APP_ENV', 'FLASK_ENV', 'YOLI_ENV', 'SECRET_KEY', 'DATABASE_URL',
            'FLASK_DEBUG', 'SESSION_COOKIE_SECURE', 'SESSION_COOKIE_HTTPONLY',
            'SESSION_COOKIE_SAMESITE', 'SESSION_LIFETIME_HOURS', 'LOG_LEVEL',
            'LOG_FILE', 'TRUSTED_HOSTS', 'BEHIND_PROXY', 'HSTS_ENABLED',
            'HSTS_MAX_AGE', 'MAX_CONTENT_LENGTH_BYTES', 'BACKUP_DIR',
            'ACCOUNT_RECOVERY_ENABLED', 'ACCOUNT_RECOVERY_LIFETIME_HOURS',
            'EMAIL_VERIFICATION_ENABLED')


def strong_key():
    return secrets.token_hex(32)


class EnvIsolationMixin:
    def setUp(self):
        self._original_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._original_env)


class ConfigTest(EnvIsolationMixin, unittest.TestCase):
    def test_invalid_environment_rejected(self):
        os.environ['APP_ENV'] = 'staging-de-testeo'
        with self.assertRaises(RuntimeError):
            create_app()

    def test_default_database_uri(self):
        os.environ.pop('DATABASE_URL', None)
        self.assertEqual(get_config()['SQLALCHEMY_DATABASE_URI'],
                         'sqlite:///' + str(ROOT / 'instance' / 'tienda.db'))

    def test_database_url_override_via_env(self):
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        self.assertEqual(get_config()['SQLALCHEMY_DATABASE_URI'], 'sqlite:///:memory:')
        app = create_app()
        self.assertEqual(app.config['SQLALCHEMY_DATABASE_URI'], 'sqlite:///:memory:')

    def test_development_defaults(self):
        os.environ.pop('APP_ENV', None)
        os.environ.pop('FLASK_ENV', None)
        os.environ.pop('YOLI_ENV', None)
        conf = get_config()
        self.assertEqual(conf['ENVIRONMENT'], 'development')
        self.assertFalse(conf['DEBUG'])
        self.assertFalse(conf['SESSION_COOKIE_SECURE'])
        self.assertTrue(conf['SESSION_COOKIE_HTTPONLY'])
        self.assertEqual(conf['SESSION_COOKIE_SAMESITE'], 'Lax')
        self.assertEqual(conf['LOG_LEVEL'], 'DEBUG')
        self.assertFalse(conf['BEHIND_PROXY'])
        self.assertFalse(conf['HSTS_ENABLED'])
        self.assertIsNone(conf['TRUSTED_HOSTS'])
        self.assertFalse(conf['ALLOWED_HOSTS'])
        self.assertFalse(conf['ACCOUNT_RECOVERY_ENABLED'])
        self.assertFalse(conf['EMAIL_VERIFICATION_ENABLED'])
        self.assertEqual(conf['ACCOUNT_RECOVERY_LIFETIME_HOURS'], 1)

    def test_production_security_defaults(self):
        os.environ['APP_ENV'] = 'production'
        os.environ['SECRET_KEY'] = strong_key()
        conf = get_config()
        self.assertEqual(conf['ENVIRONMENT'], 'production')
        self.assertFalse(conf['DEBUG'])
        self.assertTrue(conf['SESSION_COOKIE_SECURE'])
        self.assertEqual(conf['LOG_LEVEL'], 'INFO')
        self.assertTrue(conf['BEHIND_PROXY'])
        self.assertTrue(conf['HSTS_ENABLED'])

    def test_valid_secret_rules(self):
        for bad in ('', 'short', 'dev', 'production', 'your-secret-key-change-me-in-production',
                    'a' * 31, 1234, None):
            self.assertFalse(valid_secret(bad), repr(bad))
        self.assertTrue(valid_secret('a' * 32))
        self.assertTrue(valid_secret(strong_key()))

    def test_env_value_parsing(self):
        os.environ['HSTS_ENABLED'] = 'yes'
        os.environ['SESSION_COOKIE_HTTPONLY'] = '0'
        os.environ['MAX_CONTENT_LENGTH_BYTES'] = '1024'
        os.environ['TRUSTED_HOSTS'] = 'yoli.example.com, www.yoli.example.com'
        conf = get_config()
        self.assertTrue(conf['HSTS_ENABLED'])
        self.assertFalse(conf['SESSION_COOKIE_HTTPONLY'])
        self.assertEqual(conf['MAX_CONTENT_LENGTH'], 1024)
        self.assertEqual(conf['ALLOWED_HOSTS'], ['yoli.example.com', 'www.yoli.example.com'])
        self.assertIsNone(conf['TRUSTED_HOSTS'])

    def test_samesite_none_requires_secure(self):
        os.environ['SESSION_COOKIE_SAMESITE'] = 'None'
        os.environ.pop('SESSION_COOKIE_SECURE', None)
        os.environ.pop('APP_ENV', None)
        self.assertEqual(get_config()['SESSION_COOKIE_SAMESITE'], 'Lax')
        os.environ['SESSION_COOKIE_SECURE'] = '1'
        self.assertEqual(get_config()['SESSION_COOKIE_SAMESITE'], 'None')


class AppFactoryTest(EnvIsolationMixin, unittest.TestCase):
    def build(self, overrides=None):
        tmp = tempfile.TemporaryDirectory(dir=str(ROOT / 'instance'))
        config = {'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + tmp.name + '/prueba.db'}
        if overrides:
            config.update(overrides)
        app = create_app(config)
        with app.app_context():
            db.create_all()
        def dispose():
            with app.app_context():
                try:
                    for engine in getattr(app.extensions['sqlalchemy'], 'engines', {}).values():
                        engine.dispose()
                finally:
                    db.session.remove()
        self.addCleanup(dispose)
        self.addCleanup(tmp.cleanup)
        return app

    def test_production_requires_strong_secret(self):
        os.environ['APP_ENV'] = 'production'
        for value in (None, '', 'dev', 'short', 'production'):
            os.environ['SECRET_KEY'] = value or ''
            with self.assertRaises(RuntimeError):
                create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        os.environ['SECRET_KEY'] = strong_key()
        app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        self.assertEqual(app.config['ENVIRONMENT'], 'production')
        self.assertFalse(app.config['DEBUG'])

    def test_development_accepts_environment_secret(self):
        os.environ['APP_ENV'] = 'development'
        os.environ['SECRET_KEY'] = 'clave-de-desarrollo'
        app = self.build()
        self.assertEqual(app.config['ENVIRONMENT'], 'development')
        self.assertEqual(app.config['SECRET_KEY'], 'clave-de-desarrollo')
        self.assertFalse(app.config['SESSION_COOKIE_SECURE'])

    def test_development_generates_or_reuses_key_file(self):
        app = self.build()
        self.assertIsInstance(app.config['SECRET_KEY'], str)
        self.assertGreaterEqual(len(app.config['SECRET_KEY']), 32)

    def test_cookie_attributes_per_environment(self):
        dev = self.build()
        os.environ['APP_ENV'] = 'production'
        os.environ['SECRET_KEY'] = strong_key()
        prod = self.build()
        dev_cookie = dev.test_client().get('/').headers.get('Set-Cookie', '')
        prod_cookie = prod.test_client().get('/').headers.get('Set-Cookie', '')
        self.assertIn('HttpOnly', dev_cookie)
        self.assertNotIn('Secure', dev_cookie)
        self.assertIn('SameSite=Lax', dev_cookie)
        self.assertIn('HttpOnly', prod_cookie)
        self.assertIn('Secure', prod_cookie)
        self.assertIn('SameSite=Lax', prod_cookie)

    def test_security_headers(self):
        app = self.build()
        response = app.test_client().get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'no-referrer')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertIn('camera=()', response.headers.get('Permissions-Policy', ''))
        self.assertIn("default-src 'self'", response.headers.get('Content-Security-Policy', ''))

    def test_hsts_only_over_https(self):
        os.environ['APP_ENV'] = 'production'
        os.environ['SECRET_KEY'] = strong_key()
        app = self.build()
        client = app.test_client()
        self.assertNotIn('Strict-Transport-Security', client.get('/').headers)
        secure = client.get('/', headers={'X-Forwarded-Proto': 'https'})
        self.assertEqual(secure.headers.get('Strict-Transport-Security'),
                          f"max-age={app.config['HSTS_MAX_AGE']}; includeSubDomains")

    def test_no_hsts_over_plain_http_in_development(self):
        app = self.build()
        self.assertNotIn('Strict-Transport-Security', app.test_client().get('/').headers)

    def test_health_endpoint(self):
        app = self.build()
        response = app.test_client().get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, {'database': 'ok', 'status': 'ok'})
        self.assertEqual(response.headers.get('Cache-Control'), 'no-store')
        # No expone versión, secretos ni detalles del servidor.
        self.assertNotIn('python', response.get_data(as_text=True).lower())

    def test_trusted_hosts_enforced(self):
        os.environ['APP_ENV'] = 'development'
        os.environ['TRUSTED_HOSTS'] = 'yoli.example.com'
        app = self.build()
        client = app.test_client()
        self.assertEqual(client.get('/', headers={'Host': 'evil.example.com'}).status_code, 400)
        self.assertEqual(client.get('/', headers={'Host': 'yoli.example.com'}).status_code, 200)

    def test_error_pages_do_not_leak_tracebacks(self):
        app = self.build({'PROPAGATE_EXCEPTIONS': False})
        client = app.test_client()

        @app.route('/boom')
        def boom():
            raise RuntimeError('clave-interna-que-no-debe-mostrarse-987654')

        @app.route('/prohibido')
        def prohibido():
            from flask import abort
            abort(403)

        @app.route('/a-menudo')
        def a_menudo():
            from flask import abort
            abort(429)

        @app.route('/grande')
        def grande():
            from flask import abort
            abort(413)

        missing = client.get('/no-existe')
        self.assertEqual(missing.status_code, 404)
        self.assertIn('Esta página no está aquí', missing.get_data(as_text=True))

        boom_response = client.get('/boom')
        self.assertEqual(boom_response.status_code, 500)
        body = boom_response.get_data(as_text=True)
        self.assertNotIn('clave-interna-que-no-debe-mostrarse-987654', body)
        self.assertNotIn('Traceback', body)

        forbidden = client.get('/prohibido')
        self.assertEqual(forbidden.status_code, 403)
        self.assertIn('No tienes permiso', forbidden.get_data(as_text=True))

        limited = client.get('/a-menudo')
        self.assertEqual(limited.status_code, 429)
        self.assertIn('Demasiadas solicitudes', limited.get_data(as_text=True))

        oversized = client.get('/grande')
        self.assertEqual(oversized.status_code, 413)
        self.assertIn('supera', oversized.get_data(as_text=True).lower())


if __name__ == '__main__':
    unittest.main()