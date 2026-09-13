from flask import render_template
from . import bp
from app.services.search import public_products
from app.models import Product


@bp.get('/')
def index():
    featured = public_products().filter(Product.is_featured.is_(True)).order_by(Product.code).limit(8).all()
    if not featured:
        featured = public_products().order_by(Product.code).limit(8).all()
    return render_template('index.html', featured=featured)


@bp.get('/contacto')
def contact():
    return render_template('contact.html')


@bp.get('/favoritos')
def favorites():
    return render_template('favorites.html')
