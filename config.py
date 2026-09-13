"""Environment-based configuration. No secrets are hardcoded anywhere.

Values are resolved from the process environment (and optionally from a
project .env file) each time get_config() runs. APP_ENV selects the
environment: development, testing, staging or production.
"""
import os
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENVIRONMENTS = ('development', 'testing', 'staging', 'production')
WEAK_SECRETS = {'dev', 'development', 'debug', 'secret', 'changeme', 'password',
                'test', 'testing', 'insecure', 'example', 'production',
                'your-secret-key-change-me-in-production', '0', 'true', '1'}


def _load_dotenv(path):
    """Minimal .env loader: KEY=VALUE lines with '#' comments.

    Real environment variables always win; a project .env never overrides
    them. Values keep a possible surrounding pair of quotes stripped.
    """
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        if line.startswith('export '):
            line = line[7:].strip()
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key and not key.startswith('#') and key not in os.environ:
            os.environ[key] = value


def _truthy(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _int_env(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def detect_environment():
    raw = (os.environ.get('APP_ENV') or os.environ.get('FLASK_ENV')
           or os.environ.get('YOLI_ENV') or 'development')
    env = raw.strip().lower()
    if env not in ENVIRONMENTS:
        raise RuntimeError(f'APP_ENV inválido: {raw!r}. Use development, testing, staging o production.')
    return env


def get_config():
    """Return the active configuration as a plain dict, read at call time."""
    _load_dotenv(ROOT / '.env')
    env = detect_environment()
    is_prod = env in ('staging', 'production')
    secure = _truthy(os.environ.get('SESSION_COOKIE_SECURE'), is_prod)
    samesite = (os.environ.get('SESSION_COOKIE_SAMESITE') or 'Lax').strip()
    if samesite not in ('Lax', 'Strict', 'None'):
        samesite = 'Lax'
    if samesite == 'None' and not secure:
        samesite = 'Lax'
    debug = _truthy(os.environ.get('FLASK_DEBUG')) and env != 'production'
    return {
        'ENVIRONMENT': env,
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'SQLALCHEMY_DATABASE_URI': (os.environ.get('DATABASE_URL')
                                    or 'sqlite:///' + str(ROOT / 'instance' / 'tienda.db')),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DEBUG': debug,
        'MAX_CONTENT_LENGTH': _int_env('MAX_CONTENT_LENGTH_BYTES', 64 * 1024),
        'SESSION_COOKIE_NAME': os.environ.get('SESSION_COOKIE_NAME') or 'session',
        'SESSION_COOKIE_HTTPONLY': _truthy(os.environ.get('SESSION_COOKIE_HTTPONLY'), True),
        'SESSION_COOKIE_SECURE': secure,
        'SESSION_COOKIE_SAMESITE': samesite,
        'SESSION_REFRESH_EACH_REQUEST': False,
        'PERMANENT_SESSION_LIFETIME': timedelta(hours=_int_env('SESSION_LIFETIME_HOURS', 8)),
        'LOG_LEVEL': (os.environ.get('LOG_LEVEL') or ('INFO' if is_prod else 'DEBUG')).upper(),
        'LOG_FILE': os.environ.get('LOG_FILE') or None,
        # Flask 3.1 enlaza TRUSTED_HOSTS con la lectura de request.host y rompe
        # el render de la página de error para hosts desconocidos. Se mantiene
        # None (integración desactivada) y la lista real vive en ALLOWED_HOSTS.
        'TRUSTED_HOSTS': None,
        'ALLOWED_HOSTS': [host.strip() for host in os.environ.get('TRUSTED_HOSTS', '').split(',') if host.strip()],
        'BEHIND_PROXY': _truthy(os.environ.get('BEHIND_PROXY'), is_prod),
        'HSTS_ENABLED': _truthy(os.environ.get('HSTS_ENABLED'), is_prod),
        'HSTS_MAX_AGE': _int_env('HSTS_MAX_AGE', 31536000),
        'BACKUP_DIR': os.environ.get('BACKUP_DIR') or None,
        'CATALOG_PDF': os.environ.get('CATALOG_PDF') or str(ROOT / 'docs' / 'catalogo-productos.pdf'),
        # Cuentas de clientes. La recuperación automática y la verificación por
        # correo requieren un envío real que aún no está contratado; se mantienen
        # apagadas por defecto y nunca simulan haberse ejecutado.
        'ACCOUNT_RECOVERY_ENABLED': _truthy(os.environ.get('ACCOUNT_RECOVERY_ENABLED')),
        'ACCOUNT_RECOVERY_LIFETIME_HOURS': _int_env('ACCOUNT_RECOVERY_LIFETIME_HOURS', 1),
        'EMAIL_VERIFICATION_ENABLED': _truthy(os.environ.get('EMAIL_VERIFICATION_ENABLED')),
    }


def valid_secret(value):
    """True only for a production-grade SECRET_KEY."""
    if not isinstance(value, str):
        return False
    value = value.strip()
    if len(value) < 32:
        return False
    return value.lower() not in WEAK_SECRETS