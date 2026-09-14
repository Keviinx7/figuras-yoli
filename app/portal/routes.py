"""Public customer portal: registration, access, profile and persisted requests."""
import json
from flask import render_template, request, redirect, url_for, session, flash, current_app, abort
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash
from app.extensions import db
from app.models.commercial import Customer, AuditEvent
from app.models.customer_account import (CustomerAccount, CustomerRequest,
                                         REQUEST_STATUS_LABELS)
from app.services.customer_portal import (current_account, account_login, account_logout,
                                          customer_required, safe_next, normalize_email,
                                          clean_phone, clean_notes, login_blocked,
                                          register_login_failure, delete_login_peak,
                                          save_customer_request,
                                          PASSWORD_RULE, DUMMY_HASH)
from app.services.account_email import (throttle, send_account_email, revoke_tokens,
                                         find_token, consume_token, feature_enabled)
from app.services.mail import available
from app.services.whatsapp import clean_text, DELIVERY
from app.portal import bp


@bp.route('/registro', methods=['GET', 'POST'])
def register():
    if current_account():
        return redirect(url_for('portal.panel'))
    error = None
    if request.method == 'POST':
        throttle('register', limit=10)
        try:
            if login_blocked():
                return render_template('public/account_register.html',
                                       error='Demasiados intentos. Espere 15 minutos.'), 429
            name = clean_text(request.form.get('name', ''), 'Nombre', 180, True)
            email = normalize_email(request.form.get('email', ''))
            phone = clean_phone(request.form.get('phone', ''))
            password = request.form.get('password', '')
            if password != request.form.get('confirm', ''):
                raise ValueError('Las contraseñas no coinciden.')
            if not 12 <= len(password) <= 200:
                raise ValueError(PASSWORD_RULE)
            if CustomerAccount.query.filter_by(email=email).first():
                raise ValueError('Ya existe una cuenta con ese correo. Inicia sesión.')
            customer = Customer(name=name, phone=phone, email=email)
            db.session.add(customer)
            db.session.flush()
            account = CustomerAccount(customer_id=customer.id, email=email)
            account.set_password(password)
            db.session.add(account)
            db.session.flush()
            db.session.add(AuditEvent(entity='customer_account', entity_id=account.id,
                                      action='created'))
            db.session.commit()
            account_login(account)
            if current_app.config.get('EMAIL_VERIFICATION_ENABLED'):
                verification_notice(send_account_email(account, 'verify_email'))
                return redirect(url_for('portal.verification_pending'))
            return redirect(url_for('portal.panel'))
        except (ValueError, IntegrityError) as exc:
            db.session.rollback()
            error = str(exc) if isinstance(exc, ValueError) else 'Ya existe una cuenta con ese correo.'
    return render_template('public/account_register.html', error=error), 400 if error else 200


@bp.route('/cuenta/login', methods=['GET', 'POST'])
def login():
    if current_account():
        return redirect(url_for('portal.panel'))
    error = None
    if request.method == 'POST':
        if db.engine.dialect.name == 'sqlite':
            db.session.execute(text('BEGIN IMMEDIATE'))
        email = request.form.get('email', '').strip().lower()[:180]
        password = request.form.get('password', '')
        if login_blocked():
            db.session.rollback()
            return render_template('public/account_login.html',
                                   error='Demasiados intentos. Espere 15 minutos.'), 429
        account = CustomerAccount.query.filter_by(email=email).first()
        password_valid = check_password_hash(account.password_hash if account else DUMMY_HASH, password[:200])
        valid = account is not None and account.is_active and password_valid and len(password) <= 200
        if valid:
            delete_login_peak()
            account_login(account)
            return redirect(safe_next())
        register_login_failure()
        error = 'Correo o contraseña incorrectos.'
    return render_template('public/account_login.html', error=error,
                           next_url=request.args.get('next', '')), 401 if error else 200


@bp.post('/cuenta/logout')
def logout():
    account_logout()
    flash('Cerraste sesión de tu cuenta.')
    return redirect(url_for('portal.login'))


@bp.get('/cuenta')
@customer_required
def panel():
    account = current_account()
    requests = CustomerRequest.query.filter_by(account_id=account.id)\
        .order_by(CustomerRequest.id.desc()).limit(5).all()
    return render_template('public/account_panel.html', account=account,
                           customer=account.customer, requests=requests,
                           labels=REQUEST_STATUS_LABELS)


@bp.route('/cuenta/perfil', methods=['GET', 'POST'])
@customer_required
def profile():
    account = current_account()
    customer = account.customer
    error = None
    if request.method == 'POST':
        try:
            email = normalize_email(request.form.get('email', account.email))
            changed_email = email != account.email
            if changed_email:
                throttle('change-email', str(account.id))
                if not account.check_password(request.form.get('current_password', '')[:200]):
                    raise ValueError('Confirma tu contraseña actual para cambiar el correo.')
                if CustomerAccount.query.filter(CustomerAccount.email == email, CustomerAccount.id != account.id).first():
                    raise ValueError('Ese correo ya pertenece a una cuenta.')
                revoke_tokens(account)
                account.email = email
                account.email_verified = False
                customer.email = email
            customer.name = clean_text(request.form.get('name', ''), 'Nombre', 180, True)
            customer.phone = clean_phone(request.form.get('phone', ''))
            customer.address = clean_text(request.form.get('address', ''), 'Dirección', 300) or None
            customer.city = clean_text(request.form.get('city', ''), 'Ciudad', 100) or None
            db.session.add(AuditEvent(entity='customer', entity_id=customer.id,
                                      action='edited_by_customer'))
            db.session.commit()
            if changed_email:
                account_login(account)
                if current_app.config.get('EMAIL_VERIFICATION_ENABLED'):
                    verification_notice(send_account_email(account, 'verify_email'))
            flash('Tu perfil se actualizó.')
            return redirect(url_for('portal.profile'))
        except (ValueError, IntegrityError) as exc:
            db.session.rollback()
            error = str(exc) if isinstance(exc, ValueError) else 'Ese correo ya pertenece a una cuenta.'
    return render_template('public/account_profile.html', account=account,
                           customer=customer, error=error), 400 if error else 200


@bp.get('/cuenta/pedidos')
@customer_required
def requests_index():
    account = current_account()
    rows = CustomerRequest.query.filter_by(account_id=account.id)\
        .order_by(CustomerRequest.id.desc()).all()
    return render_template('public/account_requests.html', rows=rows,
                           labels=REQUEST_STATUS_LABELS)


@bp.get('/cuenta/pedido/<int:request_id>')
@customer_required
def request_detail(request_id):
    request_record = CustomerRequest.query.filter_by(
        id=request_id, account_id=current_account().id).first_or_404()
    return render_template('public/account_request.html', req=request_record,
                           labels=REQUEST_STATUS_LABELS)


@bp.post('/cuenta/pedidos')
@customer_required
def submit_request():
    try:
        cart = json.loads(request.form.get('cart', '[]'))
    except json.JSONDecodeError:
        cart = None
    if cart is None:
        flash('No se pudo leer tu carrito. Vuelve a revisarlo e intenta de nuevo.')
        return redirect(url_for('orders.cart'))
    account = current_account()
    try:
        request_id = save_customer_request(cart, account,
                                           request.form.get('delivery', ''),
                                           request.form.get('notes', ''))
    except ValueError as exc:
        db.session.rollback()
        flash('No pudimos guardar tu solicitud: ' + str(exc))
        return redirect(url_for('orders.cart'))
    flash('Tu solicitud quedó guardada. Te responderemos por WhatsApp o correo.')
    return redirect(url_for('portal.request_detail', request_id=request_id))


def verification_notice(result):
    if result == 'sent':
        flash('Revisa tu correo para verificar tu cuenta.')
    elif result == 'disabled':
        flash('El envío de correo no está disponible. Tu cuenta sigue guardada; puedes continuar y contactar a Yoli por WhatsApp.')
    else:
        flash('No pudimos entregar la verificación. Puedes volver a intentarlo más tarde.')


@bp.get('/cuenta/verificacion-pendiente')
@customer_required
def verification_pending():
    return render_template('public/account_verification.html', invalid=False, token=None)


@bp.post('/cuenta/reenviar-verificacion')
@customer_required
def resend_verification():
    account = current_account()
    throttle('verification', str(account.id), limit=3)
    if not account.email_verified:
        verification_notice(send_account_email(account, 'verify_email'))
    return redirect(url_for('portal.verification_pending'))


@bp.route('/cuenta/verificar/<token>', methods=['GET', 'POST'])
def verify(token):
    if not feature_enabled('verify_email'):
        abort(404)
    if request.method == 'POST':
        throttle('verify-consume', limit=20)
        account = consume_token(token, 'verify_email')
        if account:
            account.email_verified = True
            db.session.commit()
            flash('Tu correo quedó verificado. Ya puedes iniciar sesión o volver a tu cuenta.')
            return redirect(url_for('portal.panel' if current_account() else 'portal.login'))
        db.session.rollback()
    valid = find_token(token, 'verify_email') is not None
    return render_template('public/account_verification.html', invalid=not valid, token=token), 200 if valid else 400


@bp.route('/cuenta/recuperar', methods=['GET', 'POST'])
@bp.route('/cuenta/olvide-contrasena', methods=['GET', 'POST'])
def recover():
    enabled = feature_enabled('reset_password') and available()
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()[:180]
        throttle('recovery', email)
        if enabled:
            account = CustomerAccount.query.filter_by(email=email, is_active=True).first()
            if account:
                send_account_email(account, 'reset_password')
            flash('Si existe una cuenta activa con ese correo, intentaremos enviarte un enlace para restablecer tu contraseña. Revisa también spam; si no llega, inténtalo más tarde.')
        else:
            flash('La recuperación automática no está activa o el envío no está disponible. Escríbenos por WhatsApp para recibir ayuda.')
    return render_template('public/account_recover.html', enabled=enabled)


@bp.route('/cuenta/recuperar/<token>', methods=['GET', 'POST'])
@bp.route('/cuenta/restablecer/<token>', methods=['GET', 'POST'])
def reset(token):
    if not feature_enabled('reset_password'):
        abort(404)
    row = find_token(token, 'reset_password')
    if not row:
        return render_template('public/account_reset.html', invalid=True), 400
    error = None
    if request.method == 'POST':
        throttle('reset-consume', limit=20)
        password = request.form.get('password', '')
        if password != request.form.get('confirm', ''):
            error = 'Las contraseñas no coinciden.'
        elif not 12 <= len(password) <= 200:
            error = PASSWORD_RULE
        else:
            account = consume_token(token, 'reset_password')
            if not account:
                db.session.rollback()
                return render_template('public/account_reset.html', invalid=True), 400
            account.set_password(password)
            revoke_tokens(account)
            db.session.add(AuditEvent(entity='customer_account', entity_id=account.id,
                                      action='password_reset'))
            db.session.commit()
            session.clear()
            flash('Tu contraseña se restableció. Inicia sesión con tu nueva contraseña.')
            return redirect(url_for('portal.login'))
    return render_template('public/account_reset.html', invalid=False, error=error, token=token), 400 if error else 200
