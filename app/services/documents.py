"""Transactional numbering, immutable snapshots and server-side document totals."""
from datetime import datetime, timezone
from decimal import Decimal
from flask import abort
from flask_login import current_user
from app.extensions import db
from app.models import Product
from app.models.commercial import Customer,Quote,QuoteItem,Invoice,InvoiceItem,NumberSequence,CostEstimate,ProductCostRecipe
from app.services.costing import decimal_value,text_value,calculate_cost,json_decimals,precise,ZERO,money,quantize_money
from app.services.commercial import settings,record
from app.services.dates import local_today


def next_number(kind,prefix):
    # Atomic UPSERT in the SAME transaction as the document. Unique constraints are a second guard.
    if db.engine.dialect.name == 'sqlite':
        from sqlalchemy.dialects.sqlite import insert
    else:
        from sqlalchemy.dialects.postgresql import insert
    stmt=insert(NumberSequence).values(kind=kind,value=1)
    stmt=stmt.on_conflict_do_update(index_elements=['kind'],set_={'value':NumberSequence.value+1}).returning(NumberSequence.value)
    number=db.session.execute(stmt).scalar_one()
    return f'{prefix}-{number:06d}'


def snapshots(customer,business,tax):
    return ({k:getattr(customer,k) for k in ('name','identification_type','identification','email','phone','address','city')},
            {**{k:getattr(business,k) for k in ('business_name','email','phone_1','phone_2','city','branch')},'tax_name':tax.name})


@precise
def document_items(rows):
    if not isinstance(rows,list) or not 1<=len(rows)<=50: raise ValueError('Añada de 1 a 50 productos.')
    output=[]
    from app.services.production import recipe_data
    for row in rows:
        product=db.get_or_404(Product,int(row.get('product_id') or 0))
        quantity=decimal_value(row.get('quantity'),'Cantidad','10000')
        if quantity<=ZERO or quantity!=quantity.to_integral_value(): raise ValueError('Cantidad: entero mayor a cero.')
        recipe_id=row.get('recipe_id');estimate_id=row.get('estimate_id');result=None
        if recipe_id and estimate_id: raise ValueError('Seleccione una receta o un cálculo, no ambos.')
        if recipe_id:
            recipe=db.get_or_404(ProductCostRecipe,int(recipe_id))
            if not recipe.is_active: raise ValueError('La receta está inactiva. Seleccione una receta vigente.')
            if recipe.product_id!=product.id: raise ValueError('La receta pertenece a otro producto.')
            result=calculate_cost(recipe_data(recipe));cost_snapshot=dict(source='recipe',id=recipe.id,result=json_decimals(result))
        elif estimate_id:
            estimate=db.get_or_404(CostEstimate,int(estimate_id))
            if estimate.user_id!=current_user.id and current_user.role!='admin': abort(403)
            if estimate.product_id!=product.id: raise ValueError('El cálculo pertenece a otro producto o no tiene producto asociado.')
            result=calculate_cost(estimate.input_data);cost_snapshot=dict(source='estimate',id=estimate.id,result=json_decimals(result))
        else:
            if current_user.role!='admin': raise ValueError('El vendedor debe usar una receta o un cálculo guardado.')
            cost_snapshot=dict(source='manual',authorized_by=current_user.id)
        manual=row.get('unit_price','')
        if manual not in ('',None) and current_user.role!='admin': abort(403)
        if result:
            price=decimal_value(manual,'Precio manual') if manual not in ('',None) else result['unit_price']
            cost=result['production_cost']
        else:
            price=decimal_value(manual,'Precio unitario');cost=decimal_value(row.get('unit_cost'),'Costo unitario')
        surcharge=quantize_money(decimal_value(row.get('surcharge','0'),'Recargo manual'))
        discount=quantize_money(decimal_value(row.get('discount','0'),'Descuento de línea'))
        if current_user.role!='admin' and (discount>0 or surcharge>0): abort(403)
        price=quantize_money(price)
        per_unit=price+surcharge
        gross=per_unit*quantity
        if discount>gross: raise ValueError('El descuento supera el importe de la línea.')
        subtotal=quantize_money(gross-discount)
        if manual not in ('',None): cost_snapshot['manual_price']=format(price,'f');cost_snapshot['authorized_by']=current_user.id
        output.append(dict(product_id=product.id,product_code_snapshot=product.code,product_name_snapshot=product.display_name,
            quantity=quantity,requested_size=text_value(row.get('requested_size',''),'Tamaño',120),personalization=text_value(row.get('personalization',''),'Personalización',500),
            unit_cost=cost,unit_price=price,surcharge=surcharge,discount=discount,subtotal=subtotal,cost_snapshot=cost_snapshot))
    return output


@precise
def save_quote(customer_id,rows,discount='0',notes='',expires_at='',quote=None):
    business,tax=settings()
    if not business or not tax: raise ValueError('Ejecute upgrade-db.')
    customer=db.get_or_404(Customer,int(customer_id or 0));items=document_items(rows)
    discount=quantize_money(decimal_value(discount,'Descuento general'))
    if discount>0 and current_user.role!='admin': abort(403)
    subtotal=quantize_money(sum((item['subtotal'] for item in items),ZERO))
    if discount>subtotal: raise ValueError('El descuento general supera el subtotal.')
    amount=quantize_money(subtotal-discount)
    rate=tax.percentage;tax_amount=quantize_money(amount*rate/Decimal('100')) if rate is not None else None
    if quote and quote.status!='draft': raise ValueError('Solo se pueden editar borradores.')
    quote=quote or Quote(quote_number=next_number('quote',business.quote_prefix),user_id=current_user.id,status='draft')
    quote.customer_id=customer.id;quote.subtotal=subtotal;quote.discount=discount;quote.tax=tax_amount;quote.tax_percentage=rate
    quote.total=quantize_money(amount+(tax_amount or ZERO));quote.currency=business.currency
    quote.customer_snapshot,quote.business_snapshot=snapshots(customer,business,tax)
    quote.notes=text_value(notes,'Observaciones',3000)
    if expires_at:
        try: quote.expires_at=datetime.strptime(expires_at,'%Y-%m-%d')
        except (ValueError,TypeError): raise ValueError('Fecha de vencimiento inválida.')
        if quote.expires_at.date()<local_today(): raise ValueError('El vencimiento no puede estar en el pasado.')
    else: quote.expires_at=None
    quote.items=[QuoteItem(**item) for item in items]
    db.session.add(quote);db.session.flush();record('quote',quote.id,'draft_saved',quote.quote_number)
    for item in items:
        if 'manual_price' in item['cost_snapshot']:
            record('quote',quote.id,'manual_price',item['product_code_snapshot']+' · '+str(item['unit_price']))
    return quote


def require_ready(quote):
    if quote.tax_percentage is None or not quote.currency: raise ValueError('Configure moneda e impuesto y vuelva a guardar el borrador antes de continuar.')
    if quote.expires_at and quote.expires_at.date()<local_today(): raise ValueError('La cotización ha vencido. Márquela vencida y prepare una nueva.')


def quote_status(quote,target):
    allowed={'draft':{'sent','expired'},'sent':{'accepted','rejected','expired'},'accepted':set(),'rejected':set(),'expired':set(),'converted':set()}
    if target not in allowed[quote.status]: raise ValueError('Cambio de estado de cotización no permitido.')
    if target in ('sent','accepted'): require_ready(quote)
    quote.status=target;record('quote',quote.id,target,quote.quote_number)


def convert_quote(quote):
    if quote.status!='accepted': raise ValueError('Solo puede facturarse una cotización aceptada.')
    require_ready(quote)
    if Invoice.query.filter_by(quote_id=quote.id).first(): raise ValueError('La cotización ya tiene factura.')
    business,_=settings()
    invoice=Invoice(invoice_number=next_number('invoice',business.invoice_prefix),quote_id=quote.id,customer_id=quote.customer_id,user_id=current_user.id,status='draft',subtotal=quote.subtotal,discount=quote.discount,tax=quote.tax,tax_percentage=quote.tax_percentage,total=quote.total,currency=quote.currency,customer_snapshot=dict(quote.customer_snapshot),business_snapshot=dict(quote.business_snapshot),notes=quote.notes)
    keys=('product_id','product_code_snapshot','product_name_snapshot','quantity','requested_size','personalization','unit_price','surcharge','discount','subtotal')
    invoice.items=[InvoiceItem(**{k:getattr(item,k) for k in keys}) for item in quote.items]
    db.session.add(invoice);db.session.flush();quote.status='converted'
    record('invoice',invoice.id,'created_from_quote',quote.quote_number);record('quote',quote.id,'converted',invoice.invoice_number)
    return invoice


def invoice_status(invoice,target,payment_method='',reason=''):
    allowed={'draft':{'issued','cancelled'},'issued':{'paid','cancelled'},'paid':{'cancelled'},'cancelled':set()}
    if target not in allowed[invoice.status]: raise ValueError('Cambio de estado de factura no permitido.')
    business,_=settings()
    if target=='cancelled':
        if current_user.role!='admin': abort(403)
        reason=text_value(reason,'Motivo de cancelación',500,True)
    if target=='paid':
        if payment_method not in business.payment_methods: raise ValueError('Seleccione una forma de pago configurada.')
        invoice.payment_method=payment_method;invoice.paid_at=datetime.now(timezone.utc).replace(tzinfo=None)
    if target=='issued' and (not invoice.currency or invoice.tax_percentage is None): raise ValueError('Faltan moneda o impuesto.')
    invoice.status=target;record('invoice',invoice.id,target,reason or invoice.invoice_number)


def quote_message(quote):
    message=[quote.business_snapshot['business_name'],f'Cotización {quote.quote_number}',f"Cliente: {quote.customer_snapshot['name']}"]
    for item in quote.items:
        message.append(f'{item.product_code_snapshot} — {item.product_name_snapshot} × {item.quantity}: {money(item.subtotal)} {quote.currency or "moneda pendiente"}')
        if item.requested_size: message.append('Tamaño: '+item.requested_size)
        if item.personalization: message.append('Personalización: '+item.personalization)
    message.extend([f'Descuento general: {money(quote.discount)}',f'Impuesto: {money(quote.tax)}',f'Total: {money(quote.total)} {quote.currency or "moneda pendiente"}'])
    if quote.notes: message.append(quote.notes)
    if quote.expires_at: message.append('Válida hasta: '+quote.expires_at.strftime('%Y-%m-%d'))
    message.append('La aceptación se registra por separado. Documento interno.')
    return '\n'.join(message)
