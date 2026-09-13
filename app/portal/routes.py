"""Public customer portal: registration, access, profile and persisted requests."""
import json
from flask import render_template, request, redirect, url_for, session, flash, current_app
from sqlalchemy import text
from app.extensions import db
from app.models.commercial import Customer, AuditEvent
from app.models.customer_account import (CustomerAccount, CustomerRequest,
                                         REQUEST_STATUS_LABELS)
from app.services.customer_portal import (current_account, account_login, account_logout,
                                          customer_required, safe_next, normalize_email,
                                          clean_phone, clean_notes, login_blocked,
                                          register_login_failure, delete_login_peak,
                                          save_customer_request, consume_recovery_token,
                                          PASSWORD_RULE)
from app.services.whatsapp import clean_text, DELIVERY
from app.portal import bp


@bp.route('/registro', methods=['GET', 'POST'])
def register():
    if current_account():
        return redirect(url_for('portal.panel'))
    error = None
    if request.method == 'POST':
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
            return redirect(url_for('portal.panel'))
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)
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
        valid = account is not None and account.is_active and \
            account.check_password(password) and len(password) <= 200
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
            customer.name = clean_text(request.form.get('name', ''), 'Nombre', 180, True)
            customer.phone = clean_phone(request.form.get('phone', ''))
            customer.address = clean_text(request.form.get('address', ''), 'Dirección', 300) or None
            customer.city = clean_text(request.form.get('city', ''), 'Ciudad', 100) or None
            db.session.add(AuditEvent(entity='customer', entity_id=customer.id,
                                      action='edited_by_customer'))
            db.session.commit()
            flash('Tu perfil se actualizó.')
            return redirect(url_for('portal.profile'))
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)
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


@bp.route('/cuenta/recuperar', methods=['GET', 'POST'])
def recover():
    """Honest recovery: automated delivery is off until an SMTP sender exists.

    The store never claims to have emailed a link: without a provider the only
    path is to contact the team, so accounts stay safe and unguessable.
    """
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()[:180]
        account = CustomerAccount.query.filter_by(email=email).first()
        if account and account.is_active:
            db.session.add(AuditEvent(entity='customer_account', entity_id=account.id,
                                      action='recovery_requested'))
            db.session.commit()
        flash('Registramos tu solicitud. Como la recuperación automática aún no está '
              'activa, escríbenos por WhatsApp para restablecer tu acceso.')
    return render_template('public/account_recover.html')


@bp.route('/cuenta/recuperar/<token>', methods=['GET', 'POST'])
def reset(token):
    account = consume_recovery_token(token)
    if not account:
        return render_template('public/account_reset.html', invalid=True), 400
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password != request.form.get('confirm', ''):
            error = 'Las contraseñas no coinciden.'
        elif not 12 <= len(password) <= 200:
            error = PASSWORD_RULE
        else:
            account.set_password(password)
            db.session.add(AuditEvent(entity='customer_account', entity_id=account.id,
                                      action='password_reset'))
            db.session.commit()
            account_login(account)
            flash('Tu contraseña se restableció.')
            return redirect(url_for('portal.panel'))
    return render_template('public/account_reset.html', invalid=False, error=error, token=token)