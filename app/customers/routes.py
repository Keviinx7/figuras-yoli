import re
from flask import request,render_template,redirect,url_for
from sqlalchemy import or_
from app.extensions import db
from app.models.commercial import Customer,Quote,Invoice,AuditEvent
from app.models.customer_account import CustomerAccount
from app.services.commercial import record,commit
from app.services.costing import text_value
from app.admin.routes import field,form
from . import bp

FIELDS={'name':('Nombre',180),'identification_type':('Tipo de identificación',30),'identification':('Identificación',80),'email':('Correo',180),'phone':('Teléfono',50),'address':('Dirección',300),'city':('Ciudad',100),'notes':('Notas',3000)}


@bp.get('')
def index():
    q=request.args.get('q','')[:180];query=Customer.query
    if q: query=query.filter(or_(Customer.name.ilike('%'+q+'%'),Customer.identification.ilike('%'+q+'%'),Customer.phone.ilike('%'+q+'%'),Customer.email.ilike('%'+q+'%')))
    return render_template('admin/customers.html',rows=query.order_by(Customer.name).all(),term=q)


@bp.route('/nuevo',methods=['GET','POST'])
@bp.route('/<int:id>/editar',methods=['GET','POST'])
def edit(id=None):
    customer=db.get_or_404(Customer,id) if id else Customer()
    if request.method=='POST':
        data={k:text_value(request.form.get(k,''),label,limit,k=='name') for k,(label,limit) in FIELDS.items()}
        data['identification']=re.sub(r'\s+','',data['identification']).upper()
        data['email']=data['email'].lower()
        if data['email'] and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',data['email']): raise ValueError('Correo inválido.')
        if data['identification'] and not data['identification_type']: raise ValueError('Indique el tipo de identificación.')
        similar=Customer.query.filter(Customer.id!=id) if id else Customer.query
        if data['identification'] and similar.filter_by(identification=data['identification']).first(): raise ValueError('Ya existe un cliente con esa identificación.')
        matches=similar.filter(db.func.lower(Customer.name)==data['name'].lower()).all()
        for other in matches:
            same_contact=(data['email'] and other.email==data['email']) or (data['phone'] and re.sub(r'\D','',other.phone or '')==re.sub(r'\D','',data['phone']))
            if same_contact or (not data['phone'] and not data['email'] and not data['identification']): raise ValueError('Posible cliente duplicado: consulte el registro existente antes de crear otro.')
        for k,v in data.items(): setattr(customer,k,v or None)
        db.session.add(customer);db.session.flush();record('customer',customer.id,'edited' if id else 'created');commit()
        return redirect(url_for('customers.detail',id=customer.id))
    return form('Editar cliente' if id else 'Nuevo cliente',[field(k,label,getattr(customer,k), 'textarea' if k in ('notes','address') else 'email' if k=='email' else 'text',k=='name') for k,(label,_) in FIELDS.items()],note='Solo el nombre es obligatorio. Busque primero para evitar duplicados.')


@bp.get('/<int:id>')
def detail(id):
    c=db.get_or_404(Customer,id)
    return render_template('admin/customer.html',customer=c,quotes=Quote.query.filter_by(customer_id=id).order_by(Quote.id.desc()).all(),invoices=Invoice.query.filter_by(customer_id=id).order_by(Invoice.id.desc()).all(),events=AuditEvent.query.filter_by(entity='customer',entity_id=id).order_by(AuditEvent.id.desc()).all(),account=CustomerAccount.query.filter_by(customer_id=id).first())
