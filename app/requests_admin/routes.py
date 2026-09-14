"""Staff view of the customer store requests. Prices never appear here either:
the request only says what the client wants so staff can prepare a quote."""
import secrets
from flask import redirect, render_template, request, url_for
from sqlalchemy import or_, update
from app.extensions import db
from app.models.commercial import Customer
from app.models.customer_account import (CustomerAccount, CustomerRequest,
                                         REQUEST_STATUSES, REQUEST_STATUS_LABELS)
from app.services.commercial import roles_required, record, commit
from . import bp


@bp.get('')
def index():
    q = request.args.get('q', '')[:180]
    query = CustomerRequest.query.join(Customer, CustomerRequest.customer_id == Customer.id)
    filters = [Customer.name.ilike('%' + q + '%'), CustomerRequest.notes.ilike('%' + q + '%')]
    if q.isdigit():
        filters.append(CustomerRequest.id == int(q))
    if q:
        query = query.filter(or_(*filters))
    rows = query.order_by(CustomerRequest.id.desc()).all()
    return render_template('admin/requests.html', rows=rows, term=q,
                           labels=REQUEST_STATUS_LABELS)


@bp.get('/<int:request_id>')
def detail(request_id):
    req = db.get_or_404(CustomerRequest, request_id)
    return render_template('admin/request.html', req=req, labels=REQUEST_STATUS_LABELS)


@bp.post('/<int:request_id>/estado')
def set_status(request_id):
    req = db.get_or_404(CustomerRequest, request_id)
    status = request.form.get('status', '')
    if status not in REQUEST_STATUSES:
        raise ValueError('Estado inválido.')
    from app.services.mail import queue_order_email, deliver_order_mail
    changed = db.session.execute(update(CustomerRequest).where(
        CustomerRequest.id == req.id, CustomerRequest.status != status).values(status=status))
    notification = None
    if changed.rowcount:
        db.session.refresh(req)
        record('customer_request', req.id, 'status.' + status)
        notification = queue_order_email(req)
    commit()
    deliver_order_mail(notification.id if notification else None)
    return redirect(url_for('requests_admin.detail', request_id=req.id))


@bp.post('/clientes/<int:customer_id>/cuenta')
@roles_required('admin')
def toggle_account(customer_id):
    """Admin-only switch. Passwords are never shown, set nor removed from here."""
    account = CustomerAccount.query.filter_by(customer_id=customer_id).first_or_404()
    account.is_active = not account.is_active
    if not account.is_active:
        # Kill every existing customer session immediately on deactivation.
        account.session_token = secrets.token_hex(24)
        from app.services.account_email import revoke_tokens
        revoke_tokens(account)
    record('customer_account', account.id, 'activated' if account.is_active else 'deactivated')
    commit()
    return redirect(url_for('customers.detail', id=customer_id))