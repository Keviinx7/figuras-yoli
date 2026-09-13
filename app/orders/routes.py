import json
from flask import render_template, request
from . import bp
from app.services.whatsapp import validate_cart, build_message, whatsapp_url, PHONES, DELIVERY


@bp.get('/carrito')
def cart():
    return render_template('public/cart.html', delivery_options=DELIVERY)


@bp.post('/cotizacion')
def preview():
    try:
        lines = validate_cart(json.loads(request.form.get('cart', '[]')))
        message = build_message(lines, request.form.get('name', ''), request.form.get('city', ''), request.form.get('delivery', ''))
    except json.JSONDecodeError:
        return render_template('public/error.html', message='No se pudo leer el carrito. Vuelve a revisarlo e intenta de nuevo.'), 400
    except (ValueError, TypeError, RecursionError) as error:
        return render_template('public/error.html', message=str(error)), 400
    links = [(phone, whatsapp_url(phone, message)) for phone in PHONES]
    return render_template('public/quote_preview.html', message=message, links=links, long_message=len(links[0][1]) > 7000)
