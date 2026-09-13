from flask import request,render_template,redirect,url_for
from flask_login import current_user
from app.extensions import db
from app.models import Product
from app.models.commercial import Quote,Customer,ProductCostRecipe,CostEstimate,AuditEvent,Invoice
from app.services.commercial import commit
from app.services.documents import save_quote,quote_status,convert_quote,quote_message,require_ready
from urllib.parse import urlencode
from . import bp

ITEM_KEYS=('product_id','quantity','recipe_id','estimate_id','requested_size','personalization','unit_cost','unit_price','surcharge','discount')


def posted_items():
    columns={k:request.form.getlist('item_'+k) for k in ITEM_KEYS}
    count=len(columns['product_id'])
    if any(len(v)!=count for v in columns.values()): raise ValueError('Filas incompletas: revise los productos.')
    return [{k:v[i] for k,v in columns.items()} for i in range(count)]


@bp.get('')
def index():
    term=request.args.get('q','')[:120];query=Quote.query.join(Customer)
    if term: query=query.filter(db.or_(Quote.quote_number.ilike('%'+term+'%'),Customer.name.ilike('%'+term+'%')))
    return render_template('admin/documents.html',rows=query.order_by(Quote.id.desc()).all(),kind='quote',term=term)


@bp.route('/nueva',methods=['GET','POST'])
@bp.route('/<int:id>/editar',methods=['GET','POST'])
def edit(id=None):
    quote=db.get_or_404(Quote,id) if id else None
    if quote and quote.status!='draft': raise ValueError('Solo se pueden editar borradores.')
    if request.method=='POST':
        quote=save_quote(request.form.get('customer_id'),posted_items(),request.form.get('discount','0'),request.form.get('notes',''),request.form.get('expires_at',''),quote)
        commit();return redirect(url_for('quotes.detail',id=quote.id))
    estimates=CostEstimate.query
    if current_user.role!='admin': estimates=estimates.filter_by(user_id=current_user.id)
    items=[]
    if quote:
        for i in quote.items:
            row={k:str(getattr(i,k) or '') for k in ('product_id','quantity','requested_size','personalization','unit_cost','unit_price','surcharge','discount')}
            source=i.cost_snapshot
            row['recipe_id']=source['id'] if source['source']=='recipe' else ''
            row['estimate_id']=source['id'] if source['source']=='estimate' else ''
            if source['source']!='manual' and 'manual_price' not in source: row['unit_price']=''
            items.append(row)
    selected_product=request.args.get('producto',type=int)
    if not quote and selected_product:
        product=db.get_or_404(Product,selected_product)
        # Selecting a catalog product never supplies a recipe or an official price.
        items=[dict(product_id=product.id)]
    selected_recipe=request.args.get('receta',type=int)
    if not quote and selected_recipe:
        recipe=db.get_or_404(ProductCostRecipe,selected_recipe)
        items=[dict(product_id=recipe.product_id,recipe_id=recipe.id,requested_size=recipe.requested_size or '',personalization=recipe.personalization or '')]
    selected=request.args.get('calculo',type=int)
    if not quote and selected:
        estimate=db.get_or_404(CostEstimate,selected)
        if estimate.user_id!=current_user.id and current_user.role!='admin':
            from flask import abort
            abort(403)
        items=[dict(product_id=estimate.product_id,estimate_id=estimate.id,quantity=estimate.input_data.get('quantity','1'),requested_size=estimate.requested_size or '',personalization=estimate.personalization or '',discount=estimate.input_data.get('discount','0'),surcharge='0')]
    from app.services.production import recipe_preview,recipe_data
    available_recipes=ProductCostRecipe.query.filter_by(is_active=True).all()
    prices={r.id:recipe_preview(recipe_data(r),None)['price'] for r in available_recipes}
    return render_template('admin/quote_form.html',quote=quote,customers=Customer.query.order_by(Customer.name).all(),products=Product.query.order_by(Product.code).all(),recipes=available_recipes,recipe_prices=prices,estimates=estimates.order_by(CostEstimate.id.desc()).limit(100).all(),items=items or [{}],customer_id=request.args.get('cliente',type=int))


@bp.get('/<int:id>')
def detail(id):
    quote=db.get_or_404(Quote,id)
    return render_template('admin/document.html',doc=quote,kind='quote',events=AuditEvent.query.filter_by(entity='quote',entity_id=id).order_by(AuditEvent.id.desc()).all(),invoice=Invoice.query.filter_by(quote_id=id).first())


@bp.post('/<int:id>/estado')
def status(id):
    quote=db.get_or_404(Quote,id);quote_status(quote,request.form.get('status'));commit()
    return redirect(url_for('quotes.detail',id=id))


@bp.post('/<int:id>/facturar')
def convert(id):
    invoice=convert_quote(db.get_or_404(Quote,id));commit()
    return redirect(url_for('invoices.detail',id=invoice.id))


@bp.get('/<int:id>/imprimir')
def printable(id):
    return render_template('admin/print.html',doc=db.get_or_404(Quote,id),kind='quote')


@bp.get('/<int:id>/whatsapp')
def whatsapp(id):
    quote=db.get_or_404(Quote,id);require_ready(quote)
    message=quote_message(quote)
    import re
    phone=re.sub(r'\D','',quote.customer_snapshot.get('phone') or '')
    if len(phone)==10 and phone.startswith('0'): phone='593'+phone[1:]
    link='https://wa.me/'+phone+'?'+urlencode({'text':message}) if 8<=len(phone)<=15 else None
    return render_template('admin/whatsapp.html',doc=quote,message=message,link=link)
