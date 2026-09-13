import os
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(ROOT / 'instance' / 'tienda.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    ENVIRONMENT = os.environ.get('YOLI_ENV', 'development')
    MAX_CONTENT_LENGTH = 64 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '1' if ENVIRONMENT == 'production' else '0') == '1'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_REFRESH_EACH_REQUEST = False
    CATALOG_PDF = str(ROOT / 'docs' / 'catalogo-productos.pdf')
