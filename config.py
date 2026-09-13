import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(ROOT / 'instance' / 'tienda.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MAX_CONTENT_LENGTH = 64 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CATALOG_PDF = str(ROOT / 'docs' / 'catalogo-productos.pdf')
