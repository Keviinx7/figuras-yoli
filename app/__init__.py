import secrets
import os
import sqlite3
from pathlib import Path
import click
from flask import Flask, render_template, session, request, abort
from sqlalchemy import event
from app.extensions import db, login_manager
from config import Config


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if not app.config['SECRET_KEY']:
        if app.config['ENVIRONMENT'] == 'production':
            raise RuntimeError('Configure SECRET_KEY en el entorno de producción.')
        # The legacy .secret_key was tracked by Git. Never reuse it for staff sessions.
        key_file = Path(app.instance_path) / '.session_key'
        if not key_file.exists():
            with open(key_file, 'x', opener=lambda path, flags: os.open(path, flags, 0o600)) as file:
                file.write(secrets.token_hex(32))
        app.config['SECRET_KEY'] = key_file.read_text().strip()
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
    app.register_blueprint(main_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(orders_bp)
    from app.auth import bp as auth_bp
    from app.admin import bp as admin_bp
    from app.customers import bp as customers_bp
    from app.costs import bp as costs_bp
    from app.quotes import bp as quotes_bp
    from app.invoices import bp as invoices_bp
    for blueprint in (auth_bp, admin_bp, customers_bp, costs_bp, quotes_bp, invoices_bp):
        app.register_blueprint(blueprint)
    from app.services.commercial import register_cli
    from app.services.costing import money
    register_cli(app)
    app.jinja_env.filters['money'] = money

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
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(24)
        return {'categories': Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.name).all(),
                'csrf_token': session['csrf_token']}

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        if request.endpoint == 'orders.preview' or request.blueprint in ('auth','admin','customers','costs','quotes','invoices'):
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
        return render_template('public/error.html', message=error.description), error.code

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
