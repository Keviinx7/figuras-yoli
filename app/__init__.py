import secrets
import os
import sqlite3
import logging
import re
from pathlib import Path
import click
from flask import Flask, render_template, session, request, abort
from sqlalchemy import event
from werkzeug.middleware.proxy_fix import ProxyFix
from app.extensions import db, login_manager
from config import get_config, valid_secret


def configure_secret(app):
    env = app.config.get('ENVIRONMENT', 'development')
    secret = app.config.get('SECRET_KEY')
    if env in ('production', 'staging'):
        if not valid_secret(secret):
            raise RuntimeError(
                f'SECRET_KEY ausente, vacía o insegura en [{env}]. Genérela una vez con: '
                'python -c "import secrets; print(secrets.token_hex(32))" y póngala en el .env '
                'de ese entorno. Nunca reutilice la clave de desarrollo.'
            )
        # Production never writes a key file and never reuses the development key.
        return
    if not secret:
        # Development convenience: one persistent local key, never rotated each boot.
        key_file = Path(app.instance_path) / '.session_key'
        if not key_file.exists():
            with open(key_file, 'x', opener=lambda path, flags: os.open(path, flags, 0o600)) as file:
                file.write(secrets.token_hex(32))
        secret = key_file.read_text().strip()
        app.config['SECRET_KEY'] = secret


class RedactAccountLinks(logging.Filter):
    def filter(self, record):
        record.msg = re.sub(r'(/cuenta/(?:verificar|restablecer|recuperar)/)[^\s?"<>]+',
                            r'\1[redacted]', record.getMessage())
        record.args = ()
        return True


def configure_logging(app):
    level_name = (app.config.get('LOG_LEVEL') or 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)
    app.logger.setLevel(level)
    if not any(isinstance(f, RedactAccountLinks) for f in app.logger.filters):
        app.logger.addFilter(RedactAccountLinks())
    werkzeug_logger = logging.getLogger('werkzeug')
    if not any(isinstance(f, RedactAccountLinks) for f in werkzeug_logger.filters):
        werkzeug_logger.addFilter(RedactAccountLinks())
    werkzeug_logger.setLevel(logging.WARNING if app.config.get('ENVIRONMENT') in ('staging', 'production') else logging.INFO)
    # The default StreamHandler already goes to stderr so Gunicorn can capture it.
    if app.config.get('LOG_FILE'):
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(Path(app.config['LOG_FILE']), maxBytes=1_000_000, backupCount=5, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s'))
        handler.setLevel(level)
        app.logger.addHandler(handler)


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(get_config())
    if test_config:
        app.config.update(test_config)
    configure_secret(app)
    configure_logging(app)
    from app.services.mail import configure_mail
    configure_mail(app)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if app.config.get('BEHIND_PROXY'):
        # Trust the documented reverse proxy (Nginx) hop for scheme/host/client IP.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Inicie sesión para acceder al panel.'
    login_manager.session_protection = 'strong'
    from app.models.commercial import User

    @login_manager.user_loader
    def load_user(token):
        return User.query.filter_by(session_token=token, is_active=True).first()
    from app.services.search import normalize_search
    with app.app_context():
        @event.listens_for(db.engine, 'connect')
        def setup_sqlite(connection, _):
            if isinstance(connection, sqlite3.Connection):
                connection.create_function('search_normalize', 1, normalize_search, deterministic=True)
                connection.execute('PRAGMA foreign_keys=ON')
                connection.execute('PRAGMA busy_timeout=30000')
    from app.main import bp as main_bp
    from app.catalog import bp as catalog_bp
    from app.orders import bp as orders_bp
    from app.portal import bp as portal_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(portal_bp)
    from app.auth import bp as auth_bp
    from app.admin import bp as admin_bp
    from app.customers import bp as customers_bp
    from app.costs import bp as costs_bp
    from app.quotes import bp as quotes_bp
    from app.invoices import bp as invoices_bp
    from app.requests_admin import bp as requests_admin_bp
    for blueprint in (auth_bp, admin_bp, customers_bp, costs_bp, quotes_bp, invoices_bp, requests_admin_bp):
        app.register_blueprint(blueprint)
    from app.services.commercial import register_cli
    from app.services.costing import money, pct
    register_cli(app)
    from app.services.dates import localtime
    app.jinja_env.filters['localtime'] = localtime
    app.jinja_env.filters['money'] = money
    app.jinja_env.filters['pct'] = pct

    @app.before_request
    def enforce_host():
        # Compare the raw Host header against the allow-list. We never read
        # request.host here: Flask 3.1 + TRUSTED_HOSTS raises a SecurityError
        # from that property and breaks error-page rendering for bad hosts.
        hosts = app.config.get('ALLOWED_HOSTS') or []
        if hosts:
            host = (request.headers.get('Host') or request.environ.get('SERVER_NAME') or '').lower()
            name = host.split(':')[0]
            if host not in hosts and name not in hosts:
                abort(400, description='Host no autorizado.')

    @app.before_request
    def protect_post():
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            expected = session.get('csrf_token', '')
            actual = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
            if not expected or not secrets.compare_digest(expected.encode('utf-8'), actual.encode('utf-8')):
                abort(400, description='La sesión del formulario venció. Recargue la página e intente de nuevo.')

    @app.context_processor
    def common():
        from app.models import Category
        from app.services.customer_portal import current_account
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(24)
        return {'categories': Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.name).all(),
                'csrf_token': session['csrf_token'],
                'account': current_account()}

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        if app.config.get('HSTS_ENABLED') and request.is_secure:
            response.headers['Strict-Transport-Security'] = f"max-age={app.config.get('HSTS_MAX_AGE', 31536000)}; includeSubDomains"
        if request.endpoint == 'orders.preview' or request.blueprint in ('auth', 'admin', 'customers', 'costs', 'quotes', 'invoices', 'portal') or request.endpoint == 'main.health':
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(404)
    def not_found(error):
        return render_template('public/404.html'), 404

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(413)
    def bad_request(error):
        db.session.rollback()
        context = {400: ('REVISEMOS LOS DETALLES', 'No pudimos completar la solicitud', 'Volver al inicio →', 'main.index'),
                   403: ('ACCESO RESTRINGIDO', 'No tienes permiso para ver esto', 'Volver al inicio →', 'main.index'),
                   413: ('SOLICITUD DEMASIADO GRANDE', 'El formulario enviado supera el límite permitido', 'Volver al inicio →', 'main.index')}
        eyebrow, title, label, endpoint = context.get(error.code, context[400])
        return render_template('public/error.html', eyebrow=eyebrow, title=title, message=error.description,
                               button_label=label, button_endpoint=endpoint), error.code

    @app.errorhandler(429)
    @app.errorhandler(500)
    def unexpected(error):
        db.session.rollback()
        if error.code == 500:
            app.logger.exception('Error no controlado: %s', type(error).__name__)
            return render_template('public/error.html', eyebrow='ERROR INTERNO', title='Algo falló en nuestro servidor',
                                   message='Ocurrió un problema temporal. Intenta de nuevo en unos minutos; si persiste, escríbenos por WhatsApp.',
                                   button_label='Volver al inicio →', button_endpoint='main.index'), 500
        return render_template('public/error.html', eyebrow='UN MOMENTO', title='Demasiadas solicitudes',
                               message='Espera unos minutos antes de volver a intentarlo.',
                               button_label='Volver al inicio →', button_endpoint='main.index'), 429

    from app.services.catalog_importer import import_command, seed_categories
    app.cli.add_command(import_command)

    @app.cli.command('init-db')
    def init_db():
        db.create_all()
        seed_categories()
        from app.services.commercial import initialize_settings
        initialize_settings()
        click.echo('SQLite inicializado. Categorías de referencia listas; no se crearon productos.')

    return app