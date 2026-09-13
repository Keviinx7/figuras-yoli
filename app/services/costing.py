"""All economic operations run here, with 40 significant decimal digits, never float."""
from decimal import Decimal, InvalidOperation, localcontext, ROUND_HALF_UP
from functools import wraps
import re

ZERO = Decimal('0')
HUNDRED = Decimal('100')


def precise(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with localcontext() as context:
            context.prec = 40
            return function(*args, **kwargs)
    return wrapped


def decimal_value(value, label='Valor', maximum='1000000000', allow_empty=False):
    if allow_empty and value in (None, ''):
        return None
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(label + ': use texto decimal, no float.')
    raw = str(value).strip()
    if not re.fullmatch(r'\d{1,10}(?:\.\d{1,60})?', raw):
        raise ValueError(label + ': ingrese un decimal positivo con punto, hasta 60 posiciones decimales.')
    result = Decimal(raw)
    if result > Decimal(maximum):
        raise ValueError(label + ': excede el límite permitido.')
    return result


def text_value(value, label, limit=200, required=False):
    if not isinstance(value, str):
        raise ValueError(label + ': texto inválido.')
    value = value.strip()
    if len(value) > limit or (required and not value) or '\x00' in value:
        raise ValueError(label + ': revise el contenido o la longitud.')
    return value


def money(value):
    if value is None:
        return 'Pendiente'
    with localcontext() as context:
        context.prec = 50
        return format(Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), ',.2f')


def pct(value):
    if value is None:
        return ''
    with localcontext() as context:
        context.prec = 40
        return format(Decimal(value).normalize(), 'f')


def json_decimals(value):
    if isinstance(value, Decimal):
        return format(value, 'f')
    if isinstance(value, dict):
        return {k: json_decimals(v) for k,v in value.items()}
    if isinstance(value, list):
        return [json_decimals(v) for v in value]
    return value


@precise
def calculate_cost(data, tax_percentage=None):
    if not isinstance(data, dict):
        raise ValueError('La estructura de costos es inválida.')
    material_rows, indirect_rows = data.get('materials', []), data.get('indirects', [])
    if not isinstance(material_rows,list) or not isinstance(indirect_rows,list) or len(material_rows)>50 or len(indirect_rows)>30:
        raise ValueError('Máximo 50 materiales y 30 costos indirectos.')
    materials=[]
    for row in material_rows:
        if not isinstance(row,dict): raise ValueError('Material inválido.')
        name=text_value(row.get('name',''),'Material',120,True)
        unit=text_value(row.get('unit',''),'Unidad',40,True)
        quantity=decimal_value(row.get('quantity'),'Cantidad')
        cost=decimal_value(row.get('unit_cost'),'Costo unitario')
        materials.append(dict(name=name,unit=unit,quantity=quantity,unit_cost=cost,subtotal=quantity*cost))
    indirects=[]
    for row in indirect_rows:
        if not isinstance(row,dict): raise ValueError('Costo indirecto inválido.')
        indirects.append(dict(name=text_value(row.get('name',''),'Concepto',120,True),amount=decimal_value(row.get('amount'),'Costo indirecto')))
    time=decimal_value(data.get('labor_time','0'),'Tiempo')
    time_unit=data.get('labor_unit','hours')
    if time_unit not in ('hours','minutes'): raise ValueError('Unidad de tiempo inválida.')
    hours=time/Decimal('60') if time_unit=='minutes' else time
    hourly=decimal_value(data.get('hourly_cost','0'),'Costo por hora')
    method=data.get('profit_method','markup')
    percentage=decimal_value(data.get('profit_percentage','0'),'Porcentaje de ganancia', '1000')
    if method not in ('markup','margin'): raise ValueError('Seleccione recargo o margen.')
    if method=='margin' and percentage>=HUNDRED: raise ValueError('El margen sobre venta debe ser menor al 100%.')
    material_cost=sum((r['subtotal'] for r in materials),ZERO)
    labor_cost=hours*hourly
    indirect_cost=sum((r['amount'] for r in indirects),ZERO)
    production=material_cost+labor_cost+indirect_cost
    base=production*(1+percentage/HUNDRED) if method=='markup' else production/(1-percentage/HUNDRED)
    surcharge=decimal_value(data.get('surcharge','0'),'Recargo manual')
    discount=decimal_value(data.get('discount','0'),'Descuento')
    quantity=decimal_value(data.get('quantity','1'),'Cantidad de figuras','10000')
    if quantity<=ZERO or quantity!=quantity.to_integral_value(): raise ValueError('La cantidad de figuras debe ser un entero mayor a cero.')
    unit_price=base+surcharge
    gross=unit_price*quantity
    if discount>gross: raise ValueError('El descuento supera el subtotal.')
    subtotal=gross-discount
    rate=decimal_value(tax_percentage,'Impuesto','100',allow_empty=True)
    tax=subtotal*rate/HUNDRED if rate is not None else None
    return dict(materials=materials,indirects=indirects,labor_hours=hours,hourly_cost=hourly,
                materials_cost=material_cost,labor_cost=labor_cost,indirect_cost=indirect_cost,
                production_cost=production,profit_method=method,profit_percentage=percentage,
                base_price=base,surcharge=surcharge,unit_price=unit_price,quantity=quantity,
                discount=discount,subtotal=subtotal,tax_percentage=rate,tax=tax,
                total=subtotal+(tax or ZERO),estimated_profit=subtotal-production*quantity)
