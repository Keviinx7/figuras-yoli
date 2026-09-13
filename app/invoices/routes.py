from flask import render_template,request,redirect,url_for
from app.extensions import db
from app.models.commercial import Invoice,Customer,AuditEvent
from app.services.commercial import settings,commit
from app.services.documents import invoice_status
from . import bp


@bp.get('')
def index():
    term=request.args.get('q','')[:120];query=Invoice.query.join(Customer)
    if term: query=query.filter(db.or_(Invoice.invoice_number.ilike('%'+term+'%'),Customer.name.ilike('%'+term+'%')))
    return render_template('admin/documents.html',rows=query.order_by(Invoice.id.desc()).all(),kind='invoice',term=term)


@bp.get('/<int:id>')
def detail(id):
    business,_=settings()
    return render_template('admin/document.html',doc=db.get_or_404(Invoice,id),kind='invoice',events=AuditEvent.query.filter_by(entity='invoice',entity_id=id).order_by(AuditEvent.id.desc()).all(),business=business)


@bp.post('/<int:id>/estado')
def status(id):
    invoice=db.get_or_404(Invoice,id);invoice_status(invoice,request.form.get('status'),request.form.get('payment_method',''),request.form.get('reason',''));commit()
    return redirect(url_for('invoices.detail',id=id))


@bp.get('/<int:id>/imprimir')
def printable(id):
    return render_template('admin/print.html',doc=db.get_or_404(Invoice,id),kind='invoice')
