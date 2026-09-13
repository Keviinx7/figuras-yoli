from flask import render_template, jsonify
from sqlalchemy import text as sql_text
from . import bp
from app.extensions import db
from app.services.search import public_products
from app.models import Product


@bp.get('/')
def index():
    featured = public_products().filter(Product.is_featured.is_(True)).order_by(Product.code).limit(8).all()
    if not featured:
        featured = public_products().order_by(Product.code).limit(8).all()
    return render_template('public/index.html', featured=featured)


@bp.get('/contacto')
def contact():
    return render_template('public/contact.html')


@bp.get('/favoritos')
def favorites():
    return render_template('public/favorites.html')


@bp.get('/health')
def health():
    """Load-balancer / uptime probe. Never logs secrets or request details."""
    status = 'ok'
    try:
        db.session.execute(sql_text('SELECT 1'))
    except Exception:
        db.session.rollback()
        status = 'error'
    return jsonify(status='ok' if status == 'ok' else 'degraded', database=status), (200 if status == 'ok' else 503)