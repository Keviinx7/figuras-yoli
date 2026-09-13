import unicodedata
from sqlalchemy import func, or_
from app.extensions import db
from app.models import Product, Category


def normalize_search(value):
    # Decompose each character separately: Ñ remains distinct from N.
    result = []
    for char in unicodedata.normalize('NFC', value or '').casefold():
        if char == 'ñ':
            result.append(char)
        else:
            result.append(''.join(c for c in unicodedata.normalize('NFD', char)
                                  if not unicodedata.combining(c)))
    return ''.join(result)


def search_products(query, term):
    term = normalize_search(term.strip())
    if not term:
        return query
    columns = (Product.name, Product.code, Category.name)
    # SQLite uses its registered search_normalize SQL function; other
    # backends (PostgreSQL) use a parametrized, escaped ILIKE match.
    if db.engine.dialect.name == 'sqlite':
        return query.filter(or_(*(func.search_normalize(column).contains(term, autoescape=True)
                                 for column in columns)))
    pattern = '%' + term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
    return query.filter(or_(*(column.ilike(pattern, escape='\\') for column in columns)))


def public_products():
    return Product.query.join(Category).filter(Product.is_active.is_(True), Category.is_active.is_(True))