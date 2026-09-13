from urllib.parse import urlencode
from app.services.search import public_products
from app.models import Product

PHONES = ('593969080116', '593986791895')
DELIVERY = {'shipping': 'Envío (por confirmar)', 'san-gabriel': 'Retiro en Matriz San Gabriel (por confirmar)',
            'tulcan': 'Retiro en Sucursal Tulcán (por confirmar)'}


def clean_text(value, label, limit, required=False):
    if not isinstance(value, str):
        raise ValueError(f'{label}: texto inválido.')
    value = ' '.join(value.split())
    if (required and not value) or len(value) > limit:
        raise ValueError(f'{label}: complete el campo, máximo {limit} caracteres.')
    return value


def validate_cart(lines):
    if not isinstance(lines, list) or not 1 <= len(lines) <= 50:
        raise ValueError('Seleccione entre 1 y 50 líneas de productos.')
    validated = []
    for line in lines:
        if not isinstance(line, dict):
            raise ValueError('Línea de carrito inválida.')
        code = line.get('product_code')
        if not isinstance(code, str) or len(code) > 60:
            raise ValueError('Código de producto inválido.')
        product = public_products().filter(Product.code == code).first()
        if not product:
            raise ValueError(f'El producto {code} no existe o no está publicado. Revise su carrito.')
        quantity = line.get('quantity')
        if type(quantity) is not int or not 1 <= quantity <= 99:
            raise ValueError(f'{code}: la cantidad debe ser un entero entre 1 y 99.')
        size = clean_text(line.get('requested_size', ''), 'Tamaño', 120)
        personalization = clean_text(line.get('personalization', ''), 'Personalización', 500)
        if personalization and not product.allows_customization:
            raise ValueError(f'{code}: la personalización no está habilitada para este producto.')
        validated.append({'product_code': product.code, 'name': product.display_name,
                          'quantity': quantity, 'requested_size': size, 'personalization': personalization})
    return validated


def build_message(lines, name, city, delivery):
    name = clean_text(name, 'Nombre', 100, True)
    city = clean_text(city, 'Ciudad', 100, True)
    if delivery not in DELIVERY:
        raise ValueError('Seleccione una modalidad de entrega válida.')
    parts = ['Hola, Yoli Figuras de Fomix 👋', '', 'Quiero solicitar una cotización:', '']
    for line in lines:
        parts += [f'• {line["product_code"]} — {line["name"]}', f'  Cantidad: {line["quantity"]}',
                  f'  Tamaño solicitado: {line["requested_size"] or "Por definir"}']
        if line['personalization']:
            parts.append(f'  Personalización: {line["personalization"]}')
        parts.append('')
    parts += [f'Nombre: {name}', f'Ciudad: {city}', f'Modalidad: {DELIVERY[delivery]}', '',
              'Por favor confirmar:', '- precio según el tamaño solicitado y la personalización', '- disponibilidad', '- tiempo de elaboración', '- envío', '', 'Gracias.']
    return '\n'.join(parts)


def whatsapp_url(phone, message):
    if phone not in PHONES:
        raise ValueError('Número de WhatsApp inválido.')
    return 'https://wa.me/' + phone + '?' + urlencode({'text': message})
