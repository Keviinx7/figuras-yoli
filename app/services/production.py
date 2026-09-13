"""Current production inputs; document snapshots never call these on read."""
from copy import deepcopy
from decimal import Decimal
from app.extensions import db
from app.models.commercial import Material
from app.services.costing import calculate_cost, quantize_money, precise


def normalized_name(value):
    return ' '.join(value.split()).casefold()


def resolve_materials(data):
    data=deepcopy(data)
    for row in data['materials']:
        if row.get('material_id'):
            try: material_id=int(row['material_id'])
            except (ValueError,TypeError): raise ValueError('Referencia de material inválida.')
            material=db.session.get(Material,material_id)
            if not material: raise ValueError('El material vinculado ya no existe.')
            if row['unit']!=material.unit: raise ValueError('La unidad del material cambió; revise la cantidad de la receta.')
            row.update(material_id=material.id,name=material.name,unit=material.unit,unit_cost=material.unit_cost)
    return data


def recipe_data(recipe):
    return resolve_materials(dict(materials=[dict(material_id=m.material_id,name=m.name,unit=m.unit,quantity=m.quantity,unit_cost=m.unit_cost) for m in recipe.materials],
        indirects=recipe.indirect_costs,labor_time=recipe.labor_hours,labor_unit='hours',hourly_cost=recipe.hourly_cost,
        profit_method=recipe.profit_method,profit_percentage=recipe.profit_percentage,surcharge=recipe.surcharge,discount='0',quantity='1'))


@precise
def recipe_preview(data,tax):
    result=calculate_cost(data,tax.percentage if tax else None)
    price=quantize_money(result['unit_price'])
    discount=quantize_money(result['discount'])
    if discount>price*result['quantity']: raise ValueError('El descuento supera el subtotal comercial redondeado.')
    subtotal=quantize_money(price*result['quantity']-discount)
    iva=quantize_money(subtotal*result['tax_percentage']/Decimal('100')) if result['tax_percentage'] is not None else None
    return dict(cost=result['production_cost'],price=price,subtotal=subtotal,tax=iva,total=subtotal+(iva or Decimal('0')))


def canonical_unit(value):
    value=normalized_name(value)
    aliases={'hojas':'hoja','unidades':'unidad','metros':'metro','centímetros':'centímetro','centimetros':'centímetro','centimetro':'centímetro','gramos':'gramo','kilogramos':'kilogramo','mililitros':'ml','mililitro':'ml','litros':'litro','paquetes':'paquete','barras':'barra'}
    return aliases.get(value,value)
