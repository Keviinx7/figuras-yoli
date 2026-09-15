"""Customer portal logic: session helpers, validation and persisted requests.

The portal never records prices, costs or margins: public requests are the
starting point that staff later turns into an internal quote or invoice.
"""
import hashlib
import json
import re
from sqlalchemy import text
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import current_app, request, redirect, url_for, session
from flask_login import logout_user
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import Product
from app.models.commercial import Customer, LoginAttempt, AuditEvent
from app.models.customer_account import CustomerAccount, CustomerRequest, CustomerRequestItem
from app.services.search import public_products
from app.services.whatsapp import clean_text, validate_cart, DELIVERY

SESSION_ACCOUNT_ID = 'customer_account_id'
SESSION_ACCOUNT_TOKEN = 'customer_session_token'

# Constant hash only for timing-compatible password checks; never a real password.
DUMMY_HASH = generate_password_hash('dummy-hash-para-comparar-tiempo', method='scrypt')

EMAIL_PATTERN = re.compile(r'[^\s@]+@[^\s@]+\.[^\s@]+')
PHONE_PATTERN = re.compile(r'[0-9+ ()-]{7,20}')
PASSWORD_RULE = 'La contraseña debe tener entre 12 y 200 caracteres.'


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_email(value):
    email = clean_text(value, 'Correo', 180, True).lower()
    if not EMAIL_PATTERN.fullmatch(email):
        raise ValueError('Correo inválido.')
    return email


def clean_phone(value):
    phone = clean_text(value, 'Teléfono', 50, True)
    if not PHONE_PATTERN.fullmatch(phone):
        raise ValueError('Teléfono inválido.')
    return phone


def clean_notes(value):
    if not isinstance(value, str):
        raise ValueError('Notas: texto inválido.')
    value = value.strip()
    if len(value) > 3000 or '\x00' in value:
        raise ValueError('Notas: máximo 3000 caracteres.')
    return value


def current_account():
    """The authenticated CustomerAccount for this request, or None."""
    account_id = session.get(SESSION_ACCOUNT_ID)
    token = session.get(SESSION_ACCOUNT_TOKEN)
    if not account_id or not token:
        return None
    account = db.session.get(CustomerAccount, account_id)
    if not account or not account.is_active or account.session_token != token:
        return None
    return account


def customer_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_account():
            return redirect(url_for('portal.login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


def safe_next():
    target = request.args.get('next') or request.form.get('next') or ''
    if target.startswith('/') and not target.startswith('//') and '\\' not in target:
        return target
    return url_for('portal.panel')


def account_login(account):
    """Rotate the session token (invalidates prior sessions), then start fresh."""
    account.session_token = secrets.token_hex(24)
    account.last_login = now()
    db.session.commit()
    logout_user()
    session.clear()
    session[SESSION_ACCOUNT_ID] = account.id
    session[SESSION_ACCOUNT_TOKEN] = account.session_token
    session.permanent = True
    session['csrf_token'] = secrets.token_hex(24)


def account_logout():
    session.pop(SESSION_ACCOUNT_ID, None)
    session.pop(SESSION_ACCOUNT_TOKEN, None)


def _failure_key():
    return hashlib.sha256((request.remote_addr or 'local').encode()).hexdigest()


def login_blocked():
    attempt = db.session.get(LoginAttempt, _failure_key())
    return attempt and now() - attempt.window_start < timedelta(minutes=15) and attempt.failures >= 10


def register_login_failure():
    key = _failure_key()
    attempt = db.session.get(LoginAttempt, key)
    if not attempt:
        attempt = LoginAttempt(key=key, failures=0, window_start=now())
        db.session.add(attempt)
    if now() - attempt.window_start >= timedelta(minutes=15):
        attempt.window_start = now()
        attempt.failures = 0
    attempt.failures += 1
    db.session.commit()


def delete_login_peak():
    attempt = db.session.get(LoginAttempt, _failure_key())
    if attempt:
        db.session.delete(attempt)


def save_customer_request(cart_json, account, delivery, notes='', submission_key=''):
    """Validate the cart (server side) and persist a request WITHOUT any price data."""
    receipt = None
    if submission_key:
        if not re.fullmatch(r'[a-zA-Z0-9-]{16,80}', submission_key):
            raise ValueError('Identificador de envío inválido.')
        # Serialize retries before checking the receipt, including concurrent POSTs.
        if db.engine.dialect.name == 'sqlite':
            db.session.execute(text('BEGIN IMMEDIATE'))
        else:
            db.session.execute(db.select(CustomerAccount).where(
                CustomerAccount.id == account.id).with_for_update())
        prefix = f'{account.id}:{submission_key}:'
        fingerprint = hashlib.sha256(json.dumps(
            [cart_json, delivery, notes], sort_keys=True).encode()).hexdigest()
        receipt = prefix + fingerprint
        previous = AuditEvent.query.filter_by(entity='customer_request',
            action='created_by_customer').filter(AuditEvent.detail.startswith(prefix)).first()
        if previous:
            if previous.detail != receipt:
                raise ValueError('Este envío ya fue utilizado con otra solicitud.')
            request_id = previous.entity_id
            db.session.rollback()
            return request_id
    if delivery not in DELIVERY:
        raise ValueError('Seleccione una modalidad de entrega válida.')
    lines = validate_cart(cart_json)
    customer = account.customer
    if not customer:
        raise ValueError('Falta tu ficha de cliente. Actualiza tu perfil.')
    codes = [line['product_code'] for line in lines]
    products = {p.code: p for p in public_products().filter(Product.code.in_(codes)).all()}
    missing = [code for code in codes if code not in products]
    if missing:
        raise ValueError('El carrito contiene productos no publicados. Revísalo.')
    items = []
    for line in lines:
        product = products[line['product_code']]
        items.append(CustomerRequestItem(
            product_id=product.id,
            product_code_snapshot=product.code,
            product_name_snapshot=product.display_name,
            quantity=line['quantity'],
            requested_size=line['requested_size'] or None,
            personalization=line['personalization'] or None))
    request_record = CustomerRequest(
        customer_id=customer.id,
        account_id=account.id,
        delivery=delivery,
        delivery_label=DELIVERY[delivery],
        customer_snapshot={'name': customer.name, 'phone': customer.phone,
                           'email': customer.email, 'city': customer.city},
        notes=clean_notes(notes) or None)
    request_record.items = items
    db.session.add(request_record)
    db.session.flush()
    db.session.add(AuditEvent(entity='customer_request', entity_id=request_record.id,
                              action='created_by_customer', detail=receipt))
    from app.services.mail import queue_order_email, deliver_order_mail
    notification = queue_order_email(request_record)
    db.session.commit()
    request_id = request_record.id
    deliver_order_mail(notification.id if notification else None)
    return request_id


def recovery_token(account):
    from app.services.account_email import issue_token
    return issue_token(account, 'reset_password')


def consume_recovery_token(token):
    # Compatibility helper is a read-only validity check; routes consume atomically.
    from app.services.account_email import find_token
    row = find_token(token, 'reset_password')
    return db.session.get(CustomerAccount, row.account_id) if row else None
