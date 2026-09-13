import secrets
import os
import sqlite3
from pathlib import Path
import click
from flask import Flask, render_template, session, request, abort
from sqlalchemy import event
from app.extensions import db
from config import Config


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if not app.config['SECRET_KEY']:
        key_file = Path(app.instance_path) / '.secret_key'
        if not key_file.exists():
            with open(key_file, 'x', opener=lambda path, flags: os.open(path, flags, 0o600)) as file:
                file.write(secrets.token_hex(32))
        app.config['SECRET_KEY'] = key_file.read_text().strip()
    db.init_app(app)
    from app.services.search import normalize_search
    with app.app_context():
        @event.listens_for(db.engine, 'connect')
        def setup_sqlite(connection, _):
            if isinstance(connection, sqlite3.Connection):
                connection.create_function('search_normalize', 1, normalize_search, deterministic=True)
                connection.execute('PRAGMA foreign_keys=ON')
    from app.main import bp as main_bp
    from app.catalog import bp as catalog_bp
    from app.orders import bp as orders_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(orders_bp)

    @app.before_request
    def protect_post():
        if request.method == 'POST':
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
        if request.endpoint == 'orders.preview':
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(400)
    @app.errorhandler(413)
    def bad_request(error):
        return render_template('error.html', message=error.description), error.code

    from app.services.catalog_importer import import_command, seed_categories
    app.cli.add_command(import_command)

    @app.cli.command('init-db')
    def init_db():
        db.create_all()
        seed_categories()
        click.echo('SQLite inicializado. Categorías de referencia listas; no se crearon productos.')

    return app
