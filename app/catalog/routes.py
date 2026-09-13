from flask import render_template, request, jsonify, url_for, abort
from . import bp
from app.models import Category, Product
from app.services.search import public_products, search_products
from app.services.whatsapp import whatsapp_url, PHONES


@bp.get('/catalogo')
def catalog():
    term = request.args.get('q', '')[:200]
    category_slug = request.args.get('categoria', '')
    query = search_products(public_products(), term)
    if category_slug:
        query = query.filter(Category.slug == category_slug)
    page = request.args.get('page', 1, type=int)
    if page < 1:
        abort(404)
    pagination = query.order_by(Product.code).paginate(page=page, per_page=12, error_out=False)
    return render_template('catalog.html', pagination=pagination, term=term, category_slug=category_slug)


@bp.get('/categorias')
def categories():
    return render_template('categories.html')


@bp.get('/producto/<slug>')
def detail(slug):
    product = public_products().filter(Product.slug == slug).first_or_404()
    message = f'Hola, Yoli Figuras de Fomix. Quisiera consultar por {product.code} — {product.display_name}. Por favor confirmar precio, disponibilidad y personalización.'
    return render_template('product_detail.html', product=product, consultation_url=whatsapp_url(PHONES[0], message))


@bp.get('/api/productos')
def product_lookup():
    codes = request.args.getlist('code')
    if len(codes) > 100 or any(len(code) > 60 for code in codes):
        return jsonify(error='Demasiados códigos o códigos inválidos.'), 400
    products = public_products().filter(Product.code.in_(codes)).all() if codes else []
    return jsonify(products=[{'code': p.code, 'name': p.display_name, 'category': p.category.name,
                              'url': url_for('catalog.detail', slug=p.slug), 'image': url_for('static', filename=p.image_path),
                              'allows_customization': p.allows_customization} for p in products])
