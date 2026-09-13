import re
from decimal import Decimal
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from app.extensions import db
from app.models import Product,Category
from app.models.commercial import Customer,Quote,Invoice,User,AuditEvent
from app.services.commercial import roles_required,settings,record,commit
from app.services.costing import text_value,decimal_value,pct
from app.auth.routes import validate_user
from . import bp


def field(name,label,value='',kind='text',required=False,options=None):
    return dict(name=name,label=label,value=value if value is not None else '',kind=kind,required=required,options=options)


def form(title,fields,**kwargs):
    return render_template('admin/form.html',title=title,fields=fields,**kwargs)


@bp.get('')
@bp.get('/')
def dashboard():
    paid=Invoice.query.filter_by(status='paid').all()
    totals={}
    for invoice in paid: totals[invoice.currency]=totals.get(invoice.currency,Decimal('0'))+invoice.total
    return render_template('admin/dashboard.html',metrics=[('Productos',Product.query.count()),('Categorías',Category.query.count()),('Clientes',Customer.query.count()),('Cotizaciones',Quote.query.count()),('Facturas',Invoice.query.count()),('Ventas pagadas',len(paid))],sales=totals,events=AuditEvent.query.order_by(AuditEvent.id.desc()).limit(15).all())


@bp.get('/productos')
def products():
    from app.services.search import search_products
    term=request.args.get('q','')[:180]
    query=search_products(Product.query.join(Category),term)
    return render_template('admin/products.html',products=query.order_by(Product.code).all(),term=term)


@bp.route('/productos/<int:id>/editar',methods=['GET','POST'])
@roles_required('admin')
def product_edit(id):
    p=db.get_or_404(Product,id)
    if request.method=='POST':
        if request.form.get('code',p.code)!=p.code: raise ValueError('El código comercial es inmutable.')
        p.name=text_value(request.form.get('name',''),'Nombre',200) or None
        p.description=text_value(request.form.get('description',''),'Descripción',3000)
        p.size_notes=text_value(request.form.get('size_notes',''),'Medidas',1000)
        p.category_id=db.get_or_404(Category,request.form.get('category_id',type=int)).id
        for key in ('is_active','is_featured','allows_customization'): setattr(p,key,request.form.get(key)=='1')
        record('product',p.id,'edited',p.code);commit();return redirect(url_for('admin.products'))
    return form('Editar '+p.code,[field('name','Nombre',p.name),field('description','Descripción',p.description,'textarea'),field('size_notes','Notas de tamaño',p.size_notes,'textarea'),field('category_id','Categoría',p.category_id,'select',True,[(c.id,c.name) for c in Category.query.order_by(Category.name)]),*[field(k,label,getattr(p,k),'checkbox') for k,label in [('is_active','Publicado'),('is_featured','Destacado'),('allows_customization','Permite personalización')]]],note='El código '+p.code+' y sus imágenes se conservan. Los documentos emitidos mantienen sus snapshots.')


@bp.route('/categorias',methods=['GET','POST'])
@roles_required('admin')
def categories():
    if request.method=='POST':
        c=Category(name=text_value(request.form.get('name',''),'Nombre',120,True),slug=text_value(request.form.get('slug',''),'Slug',140,True),is_active=True)
        if not re.fullmatch(r'[a-z0-9-]+',c.slug): raise ValueError('Slug: letras minúsculas, números y guiones.')
        db.session.add(c);db.session.flush();record('category',c.id,'created');commit();return redirect(url_for('admin.categories'))
    return render_template('admin/categories.html',rows=Category.query.order_by(Category.sort_order,Category.name).all())


@bp.route('/categorias/<int:id>/editar',methods=['GET','POST'])
@roles_required('admin')
def category_edit(id):
    c=db.get_or_404(Category,id)
    if request.method=='POST':
        c.name=text_value(request.form.get('name',''),'Nombre',120,True)
        c.description=text_value(request.form.get('description',''),'Descripción',2000)
        c.is_active=request.form.get('is_active')=='1'
        c.sort_order=int(decimal_value(request.form.get('sort_order','0'),'Orden','10000'))
        record('category',c.id,'edited');commit();return redirect(url_for('admin.categories'))
    return form('Editar categoría',[field('name','Nombre',c.name,required=True),field('description','Descripción',c.description,'textarea'),field('sort_order','Orden',c.sort_order),field('is_active','Activa',c.is_active,'checkbox')])


@bp.route('/usuarios',methods=['GET','POST'])
@roles_required('admin')
def users():
    if request.method=='POST':
        username,email=validate_user(request.form.get('username',''),request.form.get('email',''))
        role=request.form.get('role')
        if role not in ('admin','vendedor'): raise ValueError('Rol inválido.')
        u=User(username=username,email=email or None,role=role);u.set_password(request.form.get('password',''))
        db.session.add(u);db.session.flush();record('user',u.id,'created');commit();return redirect(url_for('admin.users'))
    return render_template('admin/users.html',users=User.query.order_by(User.username).all())


@bp.route('/usuarios/<int:id>/editar',methods=['GET','POST'])
@roles_required('admin')
def user_edit(id):
    u=db.get_or_404(User,id)
    if request.method=='POST':
        role=request.form.get('role');active=request.form.get('is_active')=='1'
        if role not in ('admin','vendedor'): raise ValueError('Rol inválido.')
        if u.id==current_user.id and (not active or role!='admin'): raise ValueError('No puede desactivar ni degradar su propia cuenta.')
        if u.role=='admin' and u.is_active and (role!='admin' or not active) and User.query.filter_by(role='admin',is_active=True).count()<=1: raise ValueError('Debe quedar un administrador activo.')
        _,email=validate_user(u.username,request.form.get('email',''))
        u.email=email or None;u.role=role;u.is_active=active
        password=request.form.get('password','')
        if password: u.set_password(password)
        record('user',u.id,'edited','Rol, actividad o credenciales actualizados');commit();return redirect(url_for('admin.users'))
    return form('Usuario '+u.username,[field('email','Correo',u.email,'email'),field('role','Rol',u.role,'select',True,[('admin','Administrador'),('vendedor','Vendedor')]),field('is_active','Activo',u.is_active,'checkbox'),field('password','Nueva contraseña (opcional, mínimo 12 caracteres)','','password')])


@bp.route('/configuracion',methods=['GET','POST'])
@roles_required('admin')
def configuration():
    business,tax=settings()
    if not business or not tax: raise ValueError('Ejecute flask upgrade-db antes de configurar.')
    labels={'business_name':'Nombre del negocio','email':'Correo','phone_1':'Teléfono 1','phone_2':'Teléfono 2','city':'Matriz / ciudad','branch':'Sucursal','currency':'Moneda (código de 3 letras)','invoice_prefix':'Prefijo de facturas internas','quote_prefix':'Prefijo de cotizaciones'}
    if request.method=='POST':
        for k,label in labels.items():
            value=text_value(request.form.get(k,''),label,180,k=='business_name')
            if k=='currency' and value and not re.fullmatch(r'[A-Z]{3}',value): raise ValueError('Moneda: indique el código en tres letras mayúsculas.')
            if k.endswith('_prefix') and not re.fullmatch(r'[A-Z0-9-]{1,15}',value): raise ValueError('Prefijos: 1–15 letras mayúsculas, números o guiones.')
            setattr(business,k,value or None)
        tax.percentage=decimal_value(request.form.get('tax_percentage'),'Impuesto','100',True)
        tax.name=text_value(request.form.get('tax_name',''),'Nombre del impuesto',100,True)
        if '%' in tax.name: raise ValueError('El nombre del impuesto es una etiqueta (ej. IVA); no incluya el símbolo % ni porcentajes. El porcentaje se guarda en su propio campo.')
        for k in ('units','payment_methods'):
            values=[text_value(v,'Opción',40,True) for v in request.form.get(k,'').splitlines() if v.strip()]
            if not 1<=len(values)<=30 or len(set(values))!=len(values): raise ValueError('Ingrese de 1 a 30 opciones distintas, una por línea.')
            setattr(business,k,values)
        record('settings',1,'updated');commit();flash('Configuración guardada. Los documentos anteriores conservan sus datos.');return redirect(url_for('admin.configuration'))
    alerts=[]
    if tax.percentage is None or not business.currency:
        alerts=[dict(kind='error',text='Configuración pendiente: hasta guardar la moneda y un porcentaje de impuesto (o 0 explícito), los documentos nuevos se crean sin impuesto y no pueden enviarse ni facturarse. El impuesto no configurado no se trata como 0.')]
    else:
        alerts=[dict(kind='notice',text='Impuesto vigente para documentos nuevos: '+tax.name+' · '+pct(tax.percentage)+'%. Moneda: '+business.currency+'. Los documentos ya emitidos conservan sus snapshots y su moneda/impuesto.' )]
    return form('Configuración del negocio',[*[field(k,label,getattr(business,k),required=k=='business_name') for k,label in labels.items()],field('tax_name','Nombre del impuesto (etiqueta, ej. IVA)',tax.name,required=True),field('tax_percentage','Porcentaje de impuesto en números (ej. 15). Vacío = pendiente; 0 = sin impuesto',tax.percentage),field('units','Unidades, una por línea','\n'.join(business.units),'textarea',True),field('payment_methods','Formas de pago, una por línea','\n'.join(business.payment_methods),'textarea',True)],note='Configure moneda e impuesto antes de enviar cotizaciones o emitir facturas internas. No hay integración tributaria.',alerts=alerts)
