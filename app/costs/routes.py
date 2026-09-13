from flask import render_template,request,redirect,url_for
from flask_login import current_user
from app.extensions import db
from app.models import Product
from app.models.commercial import Material,ProductCostRecipe,ProductCostMaterial,CostEstimate
from app.services.commercial import roles_required,settings,record,commit
from app.services.costing import calculate_cost,decimal_value,text_value,json_decimals
from app.services.production import recipe_data, resolve_materials, recipe_preview, normalized_name
from . import bp


def cost_form_data():
    data={key:request.form.get(key,'0') for key in ('labor_time','hourly_cost','profit_percentage','surcharge','discount','quantity')}
    data.update(labor_unit=request.form.get('labor_unit','hours'),profit_method=request.form.get('profit_method','markup'))
    names=request.form.getlist('material_name');units=request.form.getlist('material_unit');quantities=request.form.getlist('material_quantity');costs=request.form.getlist('material_cost')
    if not len(names)==len(units)==len(quantities)==len(costs): raise ValueError('Filas de materiales incompletas.')
    data['materials']=[dict(name=n,unit=u,quantity=q,unit_cost=c) for n,u,q,c in zip(names,units,quantities,costs)]
    names_materials=names
    names=request.form.getlist('indirect_name');amounts=request.form.getlist('indirect_amount')
    if len(names)!=len(amounts): raise ValueError('Filas de costos indirectos incompletas.')
    data['indirects']=[dict(name=n,amount=a) for n,a in zip(names,amounts) if n.strip() or a.strip()]
    ids=request.form.getlist('material_id')
    if ids and len(ids)!=len(names_materials): raise ValueError('Referencias de materiales incompletas.')
    if ids:
        for row, material_id in zip(data['materials'], ids): row['material_id']=material_id
    business,_=settings()
    for row in data['materials']:
        if row['unit'] not in business.units and not row.get('material_id'): raise ValueError('Seleccione una unidad configurada; añádala primero en Configuración.')
    return resolve_materials(data)



@bp.route('',methods=['GET','POST'])
@roles_required('admin')
def calculator():
    business,tax=settings();result=None;estimate=None;commercial=None
    recipe=db.get_or_404(ProductCostRecipe,request.args.get('receta',type=int)) if request.args.get('receta') else None
    product_id=recipe.product_id if recipe else request.args.get('producto',type=int)
    data=recipe_data(recipe) if recipe else dict(materials=[],indirects=[],labor_time='',labor_unit='hours',hourly_cost='',profit_method='markup',profit_percentage='',surcharge='0',discount='0',quantity='1')
    size=recipe.requested_size if recipe else '';personalization=recipe.personalization if recipe else ''
    if request.method=='POST':
        data=cost_form_data()
        result=calculate_cost(data,tax.percentage if tax else None)
        commercial=recipe_preview(data,tax)
        product_id=request.form.get('product_id',type=int)
        if product_id: db.get_or_404(Product,product_id)
        size=text_value(request.form.get('requested_size',''),'Tamaño',120)
        personalization=text_value(request.form.get('personalization',''),'Personalización',500)
        estimate=CostEstimate(user_id=current_user.id,product_id=product_id,requested_size=size,personalization=personalization,input_data=json_decimals(data),result=json_decimals(result))
        db.session.add(estimate);db.session.flush();record('cost',estimate.id,'calculated');commit()
    return render_template('admin/costs.html',data=data,result=result,estimate=estimate,recipe=recipe,products=Product.query.order_by(Product.code).all(),product_id=product_id,size=size,personalization=personalization,materials=Material.query.filter_by(is_active=True).all(),recipes=[],commercial=commercial,business=business,tax=tax)


@bp.post('/recetas/guardar')
@roles_required('admin')
def save_recipe():
    estimate=db.get_or_404(CostEstimate,request.form.get('estimate_id',type=int))
    if not estimate.product_id: raise ValueError('Seleccione un producto en la calculadora antes de guardar la receta.')
    recipe_id=request.form.get('recipe_id',type=int)
    recipe=db.get_or_404(ProductCostRecipe,recipe_id) if recipe_id else ProductCostRecipe()
    if recipe_id and recipe.product_id!=estimate.product_id: raise ValueError('Use duplicar para cambiar el producto de una receta.')
    data=estimate.input_data;result=calculate_cost(data)
    recipe.product_id=estimate.product_id;recipe.name=text_value(request.form.get('name',''),'Nombre de receta',140,True)
    recipe.requested_size=estimate.requested_size;recipe.personalization=estimate.personalization
    recipe.labor_hours=result['labor_hours'];recipe.hourly_cost=result['hourly_cost'];recipe.indirect_costs=json_decimals(result['indirects'])
    recipe.profit_method=result['profit_method'];recipe.profit_percentage=result['profit_percentage'];recipe.surcharge=result['surcharge']
    from app.models.product import utcnow
    recipe.updated_at=utcnow()
    recipe.notes=text_value(request.form.get('notes',''),'Observaciones',3000)
    recipe.materials=[ProductCostMaterial(name=m['name'],unit=m['unit'],quantity=m['quantity'],unit_cost=m['unit_cost'],material_id=source.get('material_id') or None) for m,source in zip(result['materials'],data['materials'])]
    db.session.add(recipe);db.session.flush();record('recipe',recipe.id,'edited' if recipe_id else 'created');commit()
    return redirect(url_for('costs.calculator',receta=recipe.id))


@bp.post('/recetas/<int:id>/duplicar')
@roles_required('admin')
def duplicate(id):
    source=db.get_or_404(ProductCostRecipe,id);product=db.get_or_404(Product,request.form.get('product_id',type=int))
    recipe=ProductCostRecipe(product_id=product.id,name=text_value(request.form.get('name',''),'Nombre de receta',140,True),requested_size=source.requested_size,personalization=source.personalization,labor_hours=source.labor_hours,hourly_cost=source.hourly_cost,indirect_costs=source.indirect_costs,profit_method=source.profit_method,profit_percentage=source.profit_percentage,surcharge=source.surcharge,notes=source.notes)
    recipe.materials=[ProductCostMaterial(name=m.name,unit=m.unit,quantity=m.quantity,unit_cost=m.unit_cost,material_id=m.material_id) for m in source.materials]
    db.session.add(recipe);db.session.flush();record('recipe',recipe.id,'duplicated',f'Base: receta {id}');commit()
    return redirect(url_for('costs.calculator',receta=recipe.id))


@bp.route('/materiales',methods=['GET','POST'])
@roles_required('admin')
def materials():
    business,_=settings()
    if request.method=='POST':
        material_id=request.form.get('id',type=int)
        m=db.get_or_404(Material,material_id) if material_id else Material()
        m.name=text_value(request.form.get('name',''),'Material',120,True)
        with db.session.no_autoflush:
            if any(other.id!=m.id and normalized_name(other.name)==normalized_name(m.name) for other in Material.query.all()): raise ValueError('Ya existe un material con ese nombre; edítelo en el listado.')
        old_unit=m.unit
        m.unit=text_value(request.form.get('unit',''),'Unidad',40,True)
        if m.unit not in business.units: raise ValueError('Configure primero esa unidad en Configuración.')
        if material_id and old_unit!=m.unit and ProductCostMaterial.query.filter_by(material_id=m.id).first(): raise ValueError('Esta unidad está vinculada a recetas. Cree otro material para otra unidad; no se convierten cantidades automáticamente.')
        m.unit_cost=decimal_value(request.form.get('unit_cost'),'Costo unitario')
        m.is_active=request.form.get('is_active')=='1'
        db.session.add(m);db.session.flush();record('material',m.id,'saved');commit()
        return redirect(url_for('costs.materials'))
    term=request.args.get('q','').strip()[:120]
    order=request.args.get('order','name')
    rows=Material.query.all()
    rows=[m for m in rows if normalized_name(term) in normalized_name(m.name)]
    rows.sort(key=(lambda m:m.unit_cost) if order=='cost' else (lambda m:normalized_name(m.name)))
    page=max(1,request.args.get('page',1,type=int));total=len(rows)
    return render_template('admin/materials.html',materials=rows[(page-1)*25:page*25],business=business,term=term,order=order,page=page,total=total)


@bp.get('/recetas')
@roles_required('admin')
def recipes():
    term=request.args.get('q','').strip()[:120]
    rows=ProductCostRecipe.query.order_by(ProductCostRecipe.updated_at.desc()).all()
    rows=[r for r in rows if normalized_name(term) in normalized_name(' '.join([r.name,r.product.code,r.product.display_name,r.requested_size or '']))]
    page=max(1,request.args.get('page',1,type=int));total=len(rows)
    rows=rows[(page-1)*25:page*25]
    _,tax=settings()
    previews={r.id:recipe_preview(recipe_data(r),tax) for r in rows}
    return render_template('admin/recipes.html',recipes=rows,previews=previews,term=term,page=page,total=total)


@bp.post('/recetas/<int:id>/estado')
@roles_required('admin')
def recipe_status(id):
    recipe=db.get_or_404(ProductCostRecipe,id)
    if request.form.get('active') not in ('0','1'): raise ValueError('Estado inválido.')
    recipe.is_active=request.form['active']=='1'
    record('recipe',id,'activated' if recipe.is_active else 'deactivated');commit()
    return redirect(url_for('costs.recipes'))
