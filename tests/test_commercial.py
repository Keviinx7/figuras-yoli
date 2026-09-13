"""Commercial regression suite. All monetary values are synthetic test fixtures."""
import csv
import json
import secrets
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models import Product,Category
from app.models.commercial import (User,Customer,Quote,Invoice,NumberSequence,Material,ProductCostRecipe,
                                  ProductCostMaterial,CostEstimate,AuditEvent,BusinessSettings,TaxSetting)
from app.services.commercial import initialize_settings
from app.services.costing import calculate_cost,decimal_value

ROOT=Path(__file__).resolve().parents[1]


class DecimalTests(unittest.TestCase):
    def data(self,**changes):
        return dict(materials=[dict(name='Material de prueba',unit='hoja',quantity='2.5',unit_cost='0.10')],
                    indirects=[dict(name='Indirecto de prueba',amount='0.15')],labor_time='30',labor_unit='minutes',hourly_cost='4',profit_method='markup',profit_percentage='20',surcharge='0',discount='0',quantity='1',**changes)

    def test_materials_labor_indirects(self):
        result=calculate_cost(self.data(),'10')
        self.assertEqual(result['materials_cost'],Decimal('0.25'))
        self.assertEqual(result['labor_cost'],Decimal('2'))
        self.assertEqual(result['indirect_cost'],Decimal('0.15'))
        self.assertEqual(result['production_cost'],Decimal('2.40'))
        self.assertEqual(result['unit_price'],Decimal('2.880'))
        self.assertEqual(result['tax'],Decimal('0.288'))
        self.assertEqual(result['total'],Decimal('3.168'))

    def test_markup_and_margin_are_distinct(self):
        data=self.data();data['profit_method']='margin'
        result=calculate_cost(data,'10')
        self.assertEqual(result['unit_price'],Decimal('3'))
        self.assertEqual(result['total'],Decimal('3.3'))

    def test_quantity_surcharge_discount(self):
        data=self.data();data.update(quantity='3',surcharge='1',discount='0.5')
        result=calculate_cost(data,'7.5')
        self.assertEqual(result['subtotal'],Decimal('11.14'))
        self.assertEqual(result['tax'],Decimal('0.8355'))
        self.assertEqual(result['estimated_profit'],Decimal('3.94'))

    def test_unconfigured_tax_is_not_zero(self):
        self.assertIsNone(calculate_cost(self.data())['tax'])
        self.assertEqual(calculate_cost(self.data(),'0')['tax'],Decimal('0'))

    def test_invalid_money(self):
        for value in [float('nan'),0.1,True,'NaN','Infinity','-1','1e3','1,5','1_000','1000000001',None]:
            with self.subTest(value=str(value)),self.assertRaises(ValueError): decimal_value(value)

    def test_invalid_margin_quantity_discount(self):
        for patch in [dict(profit_method='margin',profit_percentage='100'),dict(quantity='0'),dict(quantity='1.2'),dict(discount='999'),dict(labor_unit='days'),dict(profit_method='unknown')]:
            data=self.data();data.update(patch)
            with self.subTest(patch=patch),self.assertRaises(ValueError): calculate_cost(data)

    def test_precision_not_rounded_for_presentation(self):
        data=self.data();data.update(labor_time='1',profit_method='margin',profit_percentage='33')
        result=calculate_cost(data)
        self.assertIsInstance(result['total'],Decimal)
        self.assertGreater(len(str(result['total']).split('.')[1]),20)


class CommercialTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'instance')
        self.app=create_app({'TESTING':True,'SECRET_KEY':secrets.token_hex(32),'SQLALCHEMY_DATABASE_URI':'sqlite:///'+self.temp.name+'/test.db'})
        self.app.instance_path=self.temp.name
        # A real request has a fresh app context; this suite holds one for DB assertions.
        @self.app.before_request
        def reset_request_user():
            from flask import g
            g.pop('_login_user',None)
        self.ctx=self.app.app_context();self.ctx.push();db.create_all();initialize_settings()
        self.password=secrets.token_urlsafe(24)
        admin=User(username='testadmin',role='admin');admin.set_password(self.password)
        seller=User(username='testseller',role='vendedor');seller.set_password(self.password)
        db.session.add_all([admin,seller]);c=Category(name='Prueba',slug='prueba');db.session.add(c);db.session.flush()
        self.product=Product(code='FY.ÑA.012',name='Producto de prueba',slug='prueba',category_id=c.id,is_active=True)
        self.other=Product(code='FY.AN.001',name='Otro de prueba',slug='otro',category_id=c.id,is_active=True)
        self.customer=Customer(name='Cliente de prueba',phone='0990000000')
        db.session.add_all([self.product,self.other,self.customer]);db.session.commit()
        self.pid=self.product.id;self.cid=self.customer.id
        self.client=self.app.test_client()

    def tearDown(self):
        db.session.remove();db.engine.dispose();self.ctx.pop();self.temp.cleanup()

    def token(self,client=None):
        client=client or self.client;client.get('/login')
        with client.session_transaction() as s: return s['csrf_token']

    def post(self,path,data=None,client=None):
        client=client or self.client
        with client.session_transaction() as s: token=s.get('csrf_token')
        if not token: token=self.token(client)
        return client.post(path,data={**(data or {}),'csrf_token':token})

    def login(self,role='admin',client=None):
        return self.post('/login',dict(username='testadmin' if role=='admin' else 'testseller',password=self.password),client)

    def configure(self):
        db.session.get(BusinessSettings,1).currency='USD'
        db.session.get(TaxSetting,1).percentage=Decimal('10')
        db.session.commit()

    def cost_payload(self):
        return dict(product_id=str(self.pid),requested_size='20 cm',personalization='Texto de prueba',material_name=['Material prueba'],material_unit=['hoja'],material_quantity=['2.5'],material_cost=['0.10'],indirect_name=['Embalaje prueba'],indirect_amount=['0.15'],labor_time='30',labor_unit='minutes',hourly_cost='4',profit_method='markup',profit_percentage='20',surcharge='0',discount='0',quantity='2')

    def quote_payload(self,estimate=None):
        return dict(customer_id=str(self.cid),discount='0',notes='Prueba',expires_at='',item_product_id=[str(self.pid)],item_quantity=['2'],item_recipe_id=[''],item_estimate_id=[str(estimate or '')],item_requested_size=['20 cm'],item_personalization=['Texto de prueba'],item_unit_cost=['1' if not estimate else ''],item_unit_price=['5' if not estimate else ''],item_surcharge=['0'],item_discount=['0'])

    def quote(self):
        response=self.post('/admin/cotizaciones/nueva',self.quote_payload())
        self.assertEqual(response.status_code,302,response.get_data(as_text=True))
        return Quote.query.order_by(Quote.id.desc()).first()

    def accepted(self):
        q=self.quote()
        for state in ['sent','accepted']:
            self.assertEqual(self.post(f'/admin/cotizaciones/{q.id}/estado',dict(status=state)).status_code,302)
        return q

    def invoice(self):
        q=self.accepted();response=self.post(f'/admin/cotizaciones/{q.id}/facturar')
        self.assertEqual(response.status_code,302)
        return Invoice.query.filter_by(quote_id=q.id).one()

    def test_login_logout_and_no_public_registration(self):
        original=self.token();self.assertEqual(self.login().status_code,302)
        with self.client.session_transaction() as s: self.assertNotEqual(original,s['csrf_token'])
        self.assertEqual(self.client.get('/admin').status_code,200)
        self.assertEqual(self.client.get('/logout').status_code,405)
        self.assertEqual(self.post('/logout').status_code,302)
        self.assertEqual(self.client.get('/admin').status_code,302)
        self.assertEqual(self.client.get('/register').status_code,404)

    def test_wrong_login_and_hash(self):
        user=User.query.filter_by(username='testadmin').one()
        self.assertNotEqual(user.password_hash,self.password)
        self.assertTrue(user.password_hash.startswith('scrypt:'))
        r=self.post('/login',dict(username='testadmin',password='wrong'))
        self.assertEqual(r.status_code,401)
        self.assertNotIn(user.password_hash,r.get_data(as_text=True))

    def test_production_requires_external_secret(self):
        with self.assertRaises(RuntimeError):
            create_app({'ENVIRONMENT':'production','SECRET_KEY':None})

    def test_login_rate_limit(self):
        for _ in range(10): self.assertEqual(self.post('/login',dict(username='missing',password='wrong')).status_code,401)
        self.assertEqual(self.login().status_code,429)

    def test_csrf_and_protected_routes(self):
        self.assertEqual(self.client.post('/login',data=dict(username='testadmin',password=self.password)).status_code,400)
        for path in ['/admin','/admin/clientes','/admin/cotizaciones','/admin/facturas','/admin/configuracion','/admin/usuarios']:
            self.assertEqual(self.client.get(path).status_code,302)
        self.login()
        for method in ['post','put','patch','delete']:
            self.assertEqual(getattr(self.client,method)('/admin/clientes/nuevo').status_code,400)
        self.assertEqual(self.client.post('/logout').status_code,400)

    def test_seller_roles(self):
        self.login('seller')
        for path in ['/admin','/admin/productos','/admin/clientes','/admin/cotizaciones','/admin/facturas']:
            self.assertEqual(self.client.get(path).status_code,200,path)
        for path in ['/admin/costos','/admin/usuarios','/admin/configuracion','/admin/categorias','/admin/costos/materiales',f'/admin/productos/{self.pid}/editar']:
            self.assertEqual(self.client.get(path).status_code,403,path)
        html=self.client.get('/admin').get_data(as_text=True)
        self.assertNotIn('href="/admin/usuarios"',html)
        self.assertEqual(self.post('/admin/usuarios',dict(username='attack')).status_code,403)

    def test_disabled_user_invalidates_session(self):
        self.login();u=User.query.filter_by(username='testadmin').one();u.is_active=False;db.session.commit()
        self.assertEqual(self.client.get('/admin').status_code,302)
        self.assertEqual(self.login().status_code,401)

    def test_password_change_invalidates_session(self):
        self.login();u=User.query.filter_by(username='testadmin').one();u.set_password(secrets.token_urlsafe(24));db.session.commit()
        self.assertEqual(self.client.get('/admin').status_code,302)

    def test_user_management_and_self_protection(self):
        self.login()
        self.assertEqual(self.post('/admin/usuarios',dict(username='thirduser',email='',role='vendedor',password=secrets.token_urlsafe(24))).status_code,302)
        u=User.query.filter_by(username='testadmin').one()
        self.assertEqual(self.post(f'/admin/usuarios/{u.id}/editar',dict(role='vendedor',email='')).status_code,400)
        self.assertTrue(u.is_active)

    def test_customer_creation_optional_fields_and_duplicate(self):
        self.login('seller')
        self.assertEqual(self.post('/admin/clientes/nuevo',dict(name='Solo nombre')).status_code,302)
        self.assertEqual(self.post('/admin/clientes/nuevo',dict(name='Solo nombre')).status_code,400)
        self.assertEqual(self.post('/admin/clientes/nuevo',dict(name='Con ID',identification='TEST-123',identification_type='Otro')).status_code,302)
        self.assertEqual(self.post('/admin/clientes/nuevo',dict(name='Otro ID',identification='TEST-123',identification_type='Otro')).status_code,400)
        self.assertEqual(self.post('/admin/clientes/nuevo',dict(name='')).status_code,400)

    def test_customer_edit_search_history(self):
        self.login()
        self.assertEqual(self.post(f'/admin/clientes/{self.cid}/editar',dict(name='Cliente editado',city='Ciudad prueba')).status_code,302)
        self.assertIn('Cliente editado',self.client.get('/admin/clientes?q=editado').get_data(as_text=True))
        self.assertIn('Historial',self.client.get(f'/admin/clientes/{self.cid}').get_data(as_text=True))

    def test_settings_unknowns_and_admin_save(self):
        business,tax=db.session.get(BusinessSettings,1),db.session.get(TaxSetting,1)
        self.assertIsNone(business.currency);self.assertIsNone(tax.percentage)
        self.login()
        data=dict(business_name='Yoli prueba',email='',phone_1='',phone_2='',city='',branch='',currency='USD',invoice_prefix='INT',quote_prefix='PRO',tax_name='Impuesto prueba',tax_percentage='7.25',units='hoja\nmetro',payment_methods='efectivo\ntransferencia')
        self.assertEqual(self.post('/admin/configuracion',data).status_code,302)
        db.session.refresh(tax);self.assertEqual(tax.percentage,Decimal('7.25'))

    def config_payload(self,**changes):
        data=dict(business_name='Yoli Figuras de Fomix',email='',phone_1='',phone_2='',city='',branch='',currency='USD',invoice_prefix='FAC',quote_prefix='COT',tax_name='IVA',tax_percentage='15',units='hoja\nmetro',payment_methods='efectivo\ntransferencia')
        data.update(changes);return data

    def test_config_iva_15_quote_exact(self):
        self.login()
        self.assertEqual(self.post('/admin/configuracion',self.config_payload()).status_code,302)
        self.assertEqual(self.post('/admin/cotizaciones/nueva',self.quote_payload()).status_code,302)
        q=Quote.query.order_by(Quote.id.desc()).first()
        self.assertEqual(q.subtotal,Decimal('10.00'))
        self.assertEqual(q.discount,Decimal('0'))
        self.assertEqual(q.tax,Decimal('1.50'))
        self.assertEqual(q.tax_percentage,Decimal('15'))
        self.assertEqual(q.total,Decimal('11.50'))
        self.assertEqual(q.currency,'USD')
        self.assertEqual(q.business_snapshot['tax_name'],'IVA')
        html=self.client.get(f'/admin/cotizaciones/{q.id}/imprimir').get_data(as_text=True)
        self.assertIn('IVA (15%)',html);self.assertIn('11.50',html)
        self.assertNotIn('provisional',html)

    def test_tax_empty_zero_and_positive_quote_level(self):
        self.login()
        one=self.quote_payload();one['item_quantity']=['1']
        # Sin configuración -> pendiente (None), nunca 0.
        self.assertEqual(self.post('/admin/cotizaciones/nueva',one).status_code,302)
        pending=Quote.query.order_by(Quote.id.desc()).first()
        self.assertIsNone(pending.tax_percentage);self.assertIsNone(pending.tax);self.assertEqual(pending.total,Decimal('5'));self.assertIsNone(pending.currency)
        # Impuesto 0 -> explícitamente sin impuesto, total = subtotal.
        self.assertEqual(self.post('/admin/configuracion',self.config_payload(tax_percentage='0')).status_code,302)
        self.assertEqual(self.post('/admin/cotizaciones/nueva',one).status_code,302)
        zero=Quote.query.order_by(Quote.id.desc()).first()
        self.assertEqual(zero.tax_percentage,Decimal('0'));self.assertEqual(zero.tax,Decimal('0'));self.assertEqual(zero.total,Decimal('5'))
        # Impuesto 15 -> cálculo real con subtotal 5.00.
        self.assertEqual(self.post('/admin/configuracion',self.config_payload()).status_code,302)
        self.assertEqual(self.post('/admin/cotizaciones/nueva',one).status_code,302)
        taxed=Quote.query.order_by(Quote.id.desc()).first()
        self.assertEqual(taxed.subtotal,Decimal('5.00'));self.assertEqual(taxed.tax,Decimal('0.75'));self.assertEqual(taxed.total,Decimal('5.75'))

    def test_historical_quote_keeps_snapshot_after_config_change(self):
        self.login()
        self.assertEqual(self.post('/admin/cotizaciones/nueva',self.quote_payload()).status_code,302)
        old=Quote.query.order_by(Quote.id.desc()).first()
        self.assertIsNone(old.tax_percentage);self.assertIsNone(old.currency);self.assertEqual(old.business_snapshot['tax_name'],'Impuesto configurado')
        self.assertEqual(self.post('/admin/configuracion',self.config_payload()).status_code,302)
        db.session.expire_all()
        self.assertIsNone(old.tax_percentage);self.assertIsNone(old.currency);self.assertEqual(old.total,Decimal('10'))
        self.assertEqual(self.post('/admin/cotizaciones/nueva',self.quote_payload()).status_code,302)
        new=Quote.query.order_by(Quote.id.desc()).first()
        self.assertEqual(new.tax_percentage,Decimal('15'));self.assertEqual(new.currency,'USD');self.assertEqual(new.total,Decimal('11.50'))

    def test_config_page_alerts(self):
        self.login()
        page=self.client.get('/admin/configuracion').get_data(as_text=True)
        self.assertIn('Configuración pendiente',page);self.assertIn('no se trata como 0',page)
        self.assertEqual(self.post('/admin/configuracion',self.config_payload()).status_code,302)
        page=self.client.get('/admin/configuracion').get_data(as_text=True)
        self.assertIn('Impuesto vigente para documentos nuevos: IVA · 15%. Moneda: USD.',page)
        self.assertNotIn('Configuración pendiente',page)

    def test_config_rejects_percent_as_tax_name(self):
        self.login()
        self.assertEqual(self.post('/admin/configuracion',self.config_payload(tax_name='Impuesto %: 15')).status_code,400)
        db.session.refresh(db.session.get(TaxSetting,1));self.assertNotEqual(db.session.get(TaxSetting,1).name,'Impuesto %: 15')
        self.assertEqual(self.post('/admin/configuracion',self.config_payload()).status_code,302)

    def test_calculator_persists_exact_values(self):
        self.login();self.configure()
        response=self.post('/admin/costos',self.cost_payload());self.assertEqual(response.status_code,200,response.get_data(as_text=True))
        e=CostEstimate.query.one();self.assertEqual(e.result['total'],'6.3360')
        self.assertIn('Recargo sobre costo',response.get_data(as_text=True))
        self.assertEqual(e.result['materials_cost'],'0.250')

    def test_recipe_save_edit_duplicate_recalculate(self):
        self.login();self.post('/admin/costos',self.cost_payload());e=CostEstimate.query.one()
        self.assertEqual(self.post('/admin/costos/recetas/guardar',dict(estimate_id=e.id,name='Receta prueba')).status_code,302)
        recipe=ProductCostRecipe.query.one();self.assertEqual(recipe.materials[0].unit_cost,Decimal('0.10'))
        self.assertEqual(self.client.get(f'/admin/costos?receta={recipe.id}').status_code,200)
        self.assertEqual(self.post(f'/admin/costos/recetas/{recipe.id}/duplicar',dict(product_id=self.other.id,name='Copia prueba')).status_code,302)
        self.assertEqual(ProductCostRecipe.query.count(),2)
        payload=self.cost_payload();payload['material_cost']=['0.20'];self.post('/admin/costos',payload)
        new=CostEstimate.query.order_by(CostEstimate.id.desc()).first()
        self.assertEqual(self.post('/admin/costos/recetas/guardar',dict(estimate_id=new.id,recipe_id=recipe.id,name='Actualizada')).status_code,302)
        db.session.refresh(recipe);self.assertEqual(recipe.materials[0].unit_cost,Decimal('0.20'))

    def test_seller_cannot_write_material_or_recipe(self):
        self.login('seller')
        self.assertEqual(self.post('/admin/costos/materiales',dict(name='M')).status_code,403)
        self.assertEqual(self.post('/admin/costos/recetas/guardar').status_code,403)

    def test_material_catalog_and_decimal_storage(self):
        self.login()
        self.assertEqual(self.post('/admin/costos/materiales',dict(name='M prueba',unit='hoja',unit_cost='0.123456789123456789',is_active='1')).status_code,302)
        db.session.expire_all();self.assertEqual(Material.query.one().unit_cost,Decimal('0.123456789123456789'))
        with sqlite3.connect(self.temp.name+'/test.db') as c:
            self.assertEqual(c.execute('select typeof(unit_cost),unit_cost from materials').fetchone(),('text','0.123456789123456789'))

    def test_quote_server_calculation_and_snapshots(self):
        self.login();self.configure();q=self.quote()
        self.assertEqual(q.subtotal,Decimal('10'));self.assertEqual(q.tax,Decimal('1'));self.assertEqual(q.total,Decimal('11'))
        self.product.name='Cambiado';self.customer.name='Cambiado';db.session.commit()
        self.assertEqual(q.items[0].product_name_snapshot,'Producto de prueba')
        self.assertEqual(q.customer_snapshot['name'],'Cliente de prueba')
        self.assertIn('FY.ÑA.012',self.client.get(f'/admin/cotizaciones/{q.id}/imprimir').get_data(as_text=True))

    def test_quote_multiple_products_and_discounts(self):
        self.login();self.configure();payload=self.quote_payload()
        for key in list(payload):
            if key.startswith('item_'): payload[key]=payload[key]*2
        payload['item_discount']=['1','0'];payload['discount']='2'
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one();self.assertEqual(len(q.items),2);self.assertEqual(q.total,Decimal('18.7'))

    def test_seller_uses_calculation_not_client_totals(self):
        self.login();self.configure();self.post('/admin/costos',self.cost_payload());e=CostEstimate.query.one()
        e.user_id=User.query.filter_by(role='vendedor').one().id;db.session.commit()
        self.post('/logout');self.login('seller')
        payload=self.quote_payload(e.id);payload['total']='0.01'
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        self.assertEqual(Quote.query.one().total,Decimal('6.34'))
        payload['item_unit_price']=['0.01'];self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,403)
        payload['item_unit_price']=[''];payload['item_discount']=['1'];self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,403)

    def test_seller_manual_quote_denied(self):
        self.login('seller');self.configure();self.assertEqual(self.post('/admin/cotizaciones/nueva',self.quote_payload()).status_code,400)

    def configure_iva(self,percentage='15'):
        business,tax=db.session.get(BusinessSettings,1),db.session.get(TaxSetting,1)
        business.currency='USD';tax.name='IVA';tax.percentage=Decimal(str(percentage));db.session.commit()

    def good_estimate(self):
        payload=dict(product_id=str(self.pid),requested_size='20 cm',personalization='Texto de prueba',
                     material_name=['Fomix prueba'],material_unit=['hoja'],material_quantity=['0.5'],material_cost=['0.60'],
                     indirect_name=[''],indirect_amount=[''],labor_time='0.75',labor_unit='hours',hourly_cost='0.25',
                     profit_method='markup',profit_percentage='100',surcharge='0',discount='0',quantity='1')
        self.assertEqual(self.post('/admin/costos',payload).status_code,200)
        return CostEstimate.query.order_by(CostEstimate.id.desc()).first()

    def good_recipe(self):
        recipe=ProductCostRecipe(product_id=self.pid,name='Receta fomix 0.975',labor_hours=Decimal('0.75'),hourly_cost=Decimal('0.25'),
                                 indirect_costs=[],profit_method='markup',profit_percentage=Decimal('100'),surcharge=Decimal('0'),notes='')
        recipe.materials=[ProductCostMaterial(name='Fomix',unit='hoja',quantity=Decimal('0.5'),unit_cost=Decimal('0.60'))]
        db.session.add(recipe);db.session.commit();return recipe

    def test_rounding_commercial_qty10(self):
        self.login();self.configure_iva()
        payload=self.quote_payload();payload['item_quantity']=['10'];payload['item_unit_price']=['0.975']
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one();item=q.items[0]
        self.assertEqual(item.unit_price,Decimal('0.98'))
        self.assertEqual(item.subtotal,Decimal('9.80'))
        self.assertEqual(q.subtotal,Decimal('9.80'));self.assertEqual(q.tax,Decimal('1.47'));self.assertEqual(q.total,Decimal('11.27'))

    def test_rounding_commercial_qty1(self):
        self.login();self.configure_iva()
        payload=self.quote_payload();payload['item_quantity']=['1'];payload['item_unit_price']=['0.975']
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one()
        self.assertEqual(q.subtotal,Decimal('0.98'));self.assertEqual(q.tax,Decimal('0.15'));self.assertEqual(q.total,Decimal('1.13'))

    def test_rounding_manual_price_qty10_no_overrounding(self):
        self.login();self.configure_iva()
        payload=self.quote_payload();payload['item_quantity']=['10'];payload['item_unit_price']=['5.00']
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one()
        self.assertEqual(q.subtotal,Decimal('50.00'));self.assertEqual(q.tax,Decimal('7.50'));self.assertEqual(q.total,Decimal('57.50'))

    def test_rounding_price_from_recipe(self):
        self.login();self.configure_iva();recipe=self.good_recipe()
        payload=self.quote_payload();payload['item_estimate_id']=[''];payload['item_recipe_id']=[str(recipe.id)]
        payload['item_unit_cost']=[''];payload['item_unit_price']=[''];payload['item_quantity']=['10']
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one();self.assertEqual(q.items[0].unit_price,Decimal('0.98'))
        self.assertEqual(q.subtotal,Decimal('9.80'));self.assertEqual(q.tax,Decimal('1.47'));self.assertEqual(q.total,Decimal('11.27'))

    def test_rounding_price_from_saved_calculation(self):
        self.login();self.configure_iva();e=self.good_estimate()
        payload=self.quote_payload(e.id);payload['item_quantity']=['10']
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one();self.assertEqual(q.items[0].unit_price,Decimal('0.98'))
        self.assertEqual(q.subtotal,Decimal('9.80'));self.assertEqual(q.tax,Decimal('1.47'));self.assertEqual(q.total,Decimal('11.27'))

    def test_rounding_surcharge_per_unit(self):
        self.login();self.configure_iva()
        payload=self.quote_payload();payload['item_quantity']=['3'];payload['item_unit_price']=['0.975'];payload['item_surcharge']=['1.50']
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one()
        self.assertEqual(q.subtotal,Decimal('7.44'));self.assertEqual(q.tax,Decimal('1.12'));self.assertEqual(q.total,Decimal('8.56'))

    def test_rounding_line_discount(self):
        self.login();self.configure_iva()
        payload=self.quote_payload();payload['item_discount']=['1.00']
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one()
        self.assertEqual(q.subtotal,Decimal('9.00'));self.assertEqual(q.tax,Decimal('1.35'));self.assertEqual(q.total,Decimal('10.35'))

    def test_rounding_general_discount(self):
        self.login();self.configure_iva()
        payload=self.quote_payload();payload['discount']='2'
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one()
        self.assertEqual(q.subtotal,Decimal('10.00'));self.assertEqual(q.discount,Decimal('2.00'));self.assertEqual(q.tax,Decimal('1.20'));self.assertEqual(q.total,Decimal('9.20'))

    def test_rounding_tax_zero(self):
        self.login();self.configure_iva('0')
        payload=self.quote_payload();payload['item_quantity']=['10'];payload['item_unit_price']=['0.975']
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one()
        self.assertEqual(q.subtotal,Decimal('9.80'));self.assertEqual(q.tax,Decimal('0'));self.assertEqual(q.total,Decimal('9.80'))

    def test_rounding_tax_pending(self):
        self.login()
        payload=self.quote_payload();payload['item_quantity']=['10'];payload['item_unit_price']=['0.975']
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one()
        self.assertIsNone(q.tax_percentage);self.assertIsNone(q.tax);self.assertEqual(q.total,Decimal('9.80'))

    def test_rounding_quote_to_invoice_exact_amounts(self):
        self.login();self.configure_iva()
        payload=self.quote_payload();payload['item_quantity']=['10'];payload['item_unit_price']=['0.975']
        self.post('/admin/cotizaciones/nueva',payload);q=Quote.query.one()
        for state in ['sent','accepted']:
            self.assertEqual(self.post(f'/admin/cotizaciones/{q.id}/estado',dict(status=state)).status_code,302)
        self.assertEqual(self.post(f'/admin/cotizaciones/{q.id}/facturar').status_code,302)
        invoice=Invoice.query.filter_by(quote_id=q.id).one()
        self.assertEqual(invoice.items[0].unit_price,Decimal('0.98'));self.assertEqual(invoice.items[0].subtotal,Decimal('9.80'))
        self.assertEqual(invoice.subtotal,q.subtotal);self.assertEqual(invoice.tax,q.tax);self.assertEqual(invoice.total,q.total)

    def test_rounding_historical_documents_keep_amounts_after_config_change(self):
        self.login();self.configure_iva()
        payload=self.quote_payload();payload['item_quantity']=['10'];payload['item_unit_price']=['0.975']
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        q=Quote.query.one()
        for state in ['sent','accepted']:
            self.post(f'/admin/cotizaciones/{q.id}/estado',dict(status=state))
        self.post(f'/admin/cotizaciones/{q.id}/facturar');invoice=Invoice.query.filter_by(quote_id=q.id).one()
        stored=(q.subtotal,q.tax,q.total,invoice.subtotal,invoice.tax,invoice.total)
        self.assertEqual(self.post('/admin/configuracion',self.config_payload(tax_percentage='7.25')).status_code,302)
        db.session.expire_all()
        self.assertEqual((q.subtotal,q.tax,q.total,invoice.subtotal,invoice.tax,invoice.total),stored)
        html=self.client.get(f'/admin/cotizaciones/{q.id}/imprimir').get_data(as_text=True)
        self.assertIn('11.27',html)

    def test_wrong_product_cost_reference_rejected(self):
        self.login();self.configure();self.post('/admin/costos',self.cost_payload());e=CostEstimate.query.one()
        payload=self.quote_payload(e.id);payload['item_product_id']=[str(self.other.id)]
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,400)
        self.assertEqual(Quote.query.count(),0)

    def test_pending_settings_blocks_sending(self):
        self.login();q=self.quote();self.assertIsNone(q.tax)
        self.assertEqual(self.post(f'/admin/cotizaciones/{q.id}/estado',dict(status='sent')).status_code,400)
        self.assertEqual(self.post(f'/admin/cotizaciones/{q.id}/facturar').status_code,400)

    def test_quote_state_transitions_and_whatsapp_do_not_accept(self):
        self.login();self.configure();q=self.quote()
        self.assertEqual(self.client.get(f'/admin/cotizaciones/{q.id}/whatsapp').status_code,200)
        db.session.refresh(q);self.assertEqual(q.status,'draft')
        self.assertEqual(self.post(f'/admin/cotizaciones/{q.id}/estado',dict(status='accepted')).status_code,400)
        self.assertEqual(self.post(f'/admin/cotizaciones/{q.id}/estado',dict(status='sent')).status_code,302)
        self.assertEqual(self.client.get(f'/admin/cotizaciones/{q.id}/editar').status_code,400)

    def test_invoice_conversion_payment_cancel_history(self):
        self.login();self.configure();invoice=self.invoice()
        self.assertEqual(invoice.total,Decimal('11'));self.assertEqual(invoice.quote.status,'converted')
        self.assertEqual(self.post(f'/admin/cotizaciones/{invoice.quote_id}/facturar').status_code,400)
        self.assertEqual(self.post(f'/admin/facturas/{invoice.id}/estado',dict(status='paid',payment_method='efectivo')).status_code,400)
        self.assertEqual(self.post(f'/admin/facturas/{invoice.id}/estado',dict(status='issued')).status_code,302)
        self.assertEqual(self.post(f'/admin/facturas/{invoice.id}/estado',dict(status='paid',payment_method='inventado')).status_code,400)
        self.assertEqual(self.post(f'/admin/facturas/{invoice.id}/estado',dict(status='paid',payment_method='efectivo')).status_code,302)
        self.assertEqual(self.post(f'/admin/facturas/{invoice.id}/estado',dict(status='cancelled',reason='Corrección de prueba')).status_code,302)
        self.assertEqual(Invoice.query.count(),1);self.assertGreaterEqual(AuditEvent.query.filter_by(entity='invoice',entity_id=invoice.id).count(),4)
        with self.client.session_transaction() as session:
            csrf=session['csrf_token']
        self.assertEqual(self.client.delete(f'/admin/facturas/{invoice.id}',headers={'X-CSRF-Token':csrf}).status_code,405)

    def test_seller_can_issue_pay_but_not_cancel(self):
        self.login();self.configure();invoice=self.invoice();self.post('/logout');self.login('seller')
        self.assertEqual(self.post(f'/admin/facturas/{invoice.id}/estado',dict(status='issued')).status_code,302)
        self.assertEqual(self.post(f'/admin/facturas/{invoice.id}/estado',dict(status='paid',payment_method='transferencia')).status_code,302)
        self.assertEqual(self.post(f'/admin/facturas/{invoice.id}/estado',dict(status='cancelled',reason='Prueba')).status_code,403)

    def test_printable_internal_disclaimer_and_no_private_cost(self):
        self.login();self.configure();invoice=self.invoice()
        response=self.client.get(f'/admin/facturas/{invoice.id}/imprimir')
        self.assertEqual(response.status_code,200)
        self.assertIn('Documento interno / no constituye comprobante electrónico autorizado',response.get_data(as_text=True))
        self.assertNotIn('unit_cost',response.get_data(as_text=True))
        self.assertEqual(response.headers['Cache-Control'],'no-store')

    def test_numbers_unique_and_failed_transactions_do_not_create_documents(self):
        self.login();self.configure();q1=self.quote();q2=self.quote()
        self.assertEqual(q1.quote_number,'COT-000001');self.assertEqual(q2.quote_number,'COT-000002')
        payload=self.quote_payload();payload['discount']='999'
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,400)
        self.assertEqual(Quote.query.count(),2)
        self.assertEqual(self.quote().quote_number,'COT-000003')

    def test_concurrent_conversion_creates_one_invoice(self):
        self.login();self.configure();qid=self.accepted().id;db.session.remove()
        def convert():
            with self.app.app_context():
                client=self.app.test_client()
                self.token(client);self.login(client=client)
                response=self.post(f'/admin/cotizaciones/{qid}/facturar',client=client)
                db.session.remove()
                return response.status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses=list(pool.map(lambda _:convert(),range(2)))
        self.assertEqual(sorted(statuses),[302,400])
        self.assertEqual(Invoice.query.count(),1)
        self.assertEqual(db.session.get(NumberSequence,'invoice').value,1)

    def test_catalog_codes_not_editable(self):
        self.login();code=self.product.code
        self.assertEqual(self.post(f'/admin/productos/{self.pid}/editar',dict(code='FY.NA.012')).status_code,400)
        self.assertEqual(db.session.get(Product,self.pid).code,code)

    def test_cli_user_no_fixed_password_and_additive_upgrade(self):
        runner=self.app.test_cli_runner()
        result=runner.invoke(args=['upgrade-db']);self.assertEqual(result.exit_code,0,result.output)
        self.assertEqual(Product.query.count(),2)
        password=secrets.token_urlsafe(24)
        result=runner.invoke(args=['create-user','--username','cliuser','--role','vendedor'],input=password+'\n'+password+'\n')
        self.assertEqual(result.exit_code,0,result.output)
        self.assertNotIn(password,result.output);self.assertTrue(User.query.filter_by(username='cliuser').one().check_password(password))

    def test_all_admin_get_templates(self):
        self.login();self.configure()
        for path in ['/admin','/admin/productos','/admin/categorias','/admin/clientes','/admin/clientes/nuevo','/admin/costos','/admin/costos/materiales','/admin/cotizaciones','/admin/cotizaciones/nueva','/admin/facturas','/admin/usuarios','/admin/configuracion',f'/admin/productos/{self.pid}/editar']:
            self.assertEqual(self.client.get(path).status_code,200,path)

    def test_production_catalog_preserved(self):
        baseline=json.loads((ROOT/'docs/commercial/catalog-baseline.json').read_text())
        with sqlite3.connect('file:'+str(ROOT/'instance/tienda.db')+'?mode=ro',uri=True) as c:
            for table,rows in baseline['tables'].items():
                self.assertEqual([list(r) for r in c.execute('select * from '+table+' order by id')],rows)
            self.assertEqual(c.execute('select count(*) from products').fetchone()[0],173)
            self.assertEqual(c.execute("select count(*) from products where code like '%Ñ%'").fetchone()[0],28)

    def test_linked_material_refresh_and_immutable_documents(self):
        from app.services.production import recipe_data
        self.login();self.configure_iva()
        material=Material(name='TEST material vigente',unit='hoja',unit_cost=Decimal('0.60'),is_active=True)
        db.session.add(material);db.session.commit()
        data=self.cost_payload();data.update(material_id=[str(material.id)],material_name=[material.name],material_quantity=['0.5'],material_cost=['999'])
        self.assertEqual(self.post('/admin/costos',data).status_code,200)
        estimate=CostEstimate.query.one()
        self.assertEqual(estimate.input_data['materials'][0]['unit_cost'],'0.60')
        self.assertEqual(self.post('/admin/costos/recetas/guardar',dict(estimate_id=estimate.id,name='TEST vinculada')).status_code,302)
        recipe=ProductCostRecipe.query.one()
        self.assertEqual(recipe.materials[0].material_id,material.id)
        payload=self.quote_payload(estimate.id)
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        quote=Quote.query.one();snapshot=json.dumps(quote.items[0].cost_snapshot,sort_keys=True);amounts=(quote.subtotal,quote.tax,quote.total)
        quote.status='accepted';db.session.commit()
        self.assertEqual(self.post(f'/admin/cotizaciones/{quote.id}/facturar').status_code,302)
        invoice=Invoice.query.one()
        self.assertEqual(self.post('/admin/costos/materiales',dict(id=material.id,name=material.name,unit='hoja',unit_cost='0.75',is_active='1')).status_code,302)
        db.session.refresh(material)
        self.assertEqual(calculate_cost(recipe_data(recipe))['materials_cost'],Decimal('0.375'))
        self.assertEqual(estimate.input_data['materials'][0]['unit_cost'],'0.60')
        payload['item_estimate_id']=[''];payload['item_recipe_id']=[str(recipe.id)]
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        new=Quote.query.order_by(Quote.id.desc()).first()
        self.assertEqual(new.items[0].cost_snapshot['result']['materials_cost'],'0.375')
        db.session.refresh(quote);db.session.refresh(invoice)
        self.assertEqual(json.dumps(quote.items[0].cost_snapshot,sort_keys=True),snapshot)
        self.assertEqual((quote.subtotal,quote.tax,quote.total),amounts)
        self.assertEqual((invoice.subtotal,invoice.tax,invoice.total),amounts)
        self.assertEqual(self.post('/admin/costos/materiales',dict(id=material.id,name=material.name,unit='hoja',unit_cost='0.75')).status_code,302)
        self.assertEqual(self.client.get(f'/admin/costos?receta={recipe.id}').status_code,200)
        self.assertEqual(calculate_cost(recipe_data(recipe))['materials_cost'],Decimal('0.375'))

    def test_material_duplicates_negative_units_and_search(self):
        self.login()
        self.assertEqual(self.post('/admin/costos/materiales',dict(name='TEST Fomix',unit='hoja',unit_cost='0.60',is_active='1')).status_code,302)
        self.assertEqual(self.post('/admin/costos/materiales',dict(name=' test   fomix ',unit='hoja',unit_cost='1',is_active='1')).status_code,400)
        self.assertEqual(self.post('/admin/costos/materiales',dict(name='TEST negativo',unit='hoja',unit_cost='-1')).status_code,400)
        self.assertEqual(self.post('/admin/costos/materiales',dict(name='TEST unidad',unit='hojas',unit_cost='1')).status_code,400)
        self.assertEqual(Material.query.count(),1)
        self.assertIn('TEST Fomix',self.client.get('/admin/costos/materiales?q=fomix&order=cost').get_data(as_text=True))
        self.assertNotIn('TEST Fomix',self.client.get('/admin/costos/materiales?q=ausente').get_data(as_text=True))

    def test_recipe_activation_and_search(self):
        self.login();self.configure();recipe=self.good_recipe()
        self.assertIn(recipe.name,self.client.get('/admin/costos/recetas?q=0.975').get_data(as_text=True))
        self.assertEqual(self.post(f'/admin/costos/recetas/{recipe.id}/estado',dict(active='0')).status_code,302)
        payload=self.quote_payload();payload.update(item_unit_price=[''],item_recipe_id=[str(recipe.id)])
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,400)
        self.assertEqual(self.post(f'/admin/costos/recetas/{recipe.id}/estado',dict(active='1')).status_code,302)
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)

    def test_seller_cannot_read_or_post_production(self):
        self.login('seller')
        for path in ['/admin/costos','/admin/costos/recetas','/admin/costos/materiales']:
            self.assertEqual(self.client.get(path).status_code,403)
        self.assertEqual(self.post('/admin/costos',self.cost_payload()).status_code,403)
        self.assertEqual(CostEstimate.query.count(),0)
        html=self.client.get('/admin/cotizaciones/nueva').get_data(as_text=True)
        self.assertNotIn('Costo unitario manual',html)
        self.assertNotIn('Abrir calculadora',html)

    def test_commercial_preview_matches_rounding_policy(self):
        from app.services.production import recipe_data,recipe_preview
        self.login();self.configure_iva();recipe=self.good_recipe()
        data=recipe_data(recipe);data['quantity']='10'
        result=recipe_preview(data,db.session.get(TaxSetting,1))
        self.assertEqual((result['price'],result['subtotal'],result['tax'],result['total']),tuple(map(Decimal,['0.98','9.80','1.47','11.27'])))

    def test_local_timezone_aware_naive_and_render(self):
        from datetime import datetime,timezone
        from zoneinfo import ZoneInfo
        from app.services.dates import localtime
        expected='12/09/2026 21:30 (America/Guayaquil)'
        self.assertEqual(localtime(datetime(2026,9,13,2,30)),expected)
        self.assertEqual(localtime(datetime(2026,9,13,2,30,tzinfo=timezone.utc)),expected)
        self.assertEqual(localtime(datetime(2026,9,12,21,30,tzinfo=ZoneInfo('America/Guayaquil'))),expected)
        self.login();db.session.add(AuditEvent(entity='TEST',action='TEST',created_at=datetime(2026,9,13,2,30)));db.session.commit()
        self.assertIn(expected,self.client.get('/admin').get_data(as_text=True))

    def test_manual_price_override_audit(self):
        self.login();self.configure();recipe=self.good_recipe()
        payload=self.quote_payload();payload['item_recipe_id']=[str(recipe.id)];payload['item_unit_price']=['1.23']
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        quote=Quote.query.one()
        self.assertEqual(quote.items[0].unit_price,Decimal('1.23'))
        self.assertEqual(quote.items[0].cost_snapshot['manual_price'],'1.23')
        self.assertEqual(AuditEvent.query.filter_by(entity='quote',action='manual_price').count(),1)

    def test_backup_includes_business_data(self):
        self.login();self.configure();self.good_recipe()
        result=self.app.test_cli_runner().invoke(args=['backup-db'])
        self.assertEqual(result.exit_code,0,result.output)
        backup=next((Path(self.temp.name)/'backups').glob('*.db'))
        with sqlite3.connect(backup) as connection:
            self.assertEqual(connection.execute('pragma integrity_check').fetchone(),('ok',))
            self.assertEqual(connection.execute('select count(*) from product_cost_recipes').fetchone(),(1,))
            self.assertEqual(connection.execute('select count(*) from customers').fetchone(),(1,))

    def test_units_normalize_without_inventing_options(self):
        from app.services.production import canonical_unit
        self.assertEqual([canonical_unit(v) for v in ['Hoja','hojas','Hojas']],['hoja']*3)
        self.login()
        payload=self.config_payload();payload['units']='Hoja\nHojas'
        self.assertEqual(self.post('/admin/configuracion',payload).status_code,400)
        payload['units']='Hojas\nBarra'
        self.assertEqual(self.post('/admin/configuracion',payload).status_code,302)
        self.assertEqual(db.session.get(BusinessSettings,1).units,['hoja','barra'])

    def test_migration_adds_activity_preserving_recipe(self):
        self.login();recipe=self.good_recipe();recipe_id=recipe.id
        db.session.remove()
        with db.engine.begin() as connection:
            connection.exec_driver_sql('ALTER TABLE product_cost_recipes DROP COLUMN is_active')
        result=self.app.test_cli_runner().invoke(args=['upgrade-db'])
        self.assertEqual(result.exit_code,0,result.output)
        recipe=db.session.get(ProductCostRecipe,recipe_id)
        self.assertTrue(recipe.is_active)
        self.assertEqual(recipe.materials[0].quantity,Decimal('0.5'))

    def test_internal_material_data_never_public(self):
        self.login();self.configure();self.good_recipe()
        db.session.add(Material(name='TEST SECRETO INTERNO',unit='hoja',unit_cost=Decimal('123.456789')));db.session.commit()
        public=self.app.test_client()
        for path in ['/', '/catalogo', '/categorias', '/carrito', '/favoritos']:
            response=public.get(path);self.assertEqual(response.status_code,200)
            html=response.get_data(as_text=True)
            for secret in ['TEST SECRETO INTERNO','123.456789','hourly_cost','profit_percentage','production_cost']:
                self.assertNotIn(secret,html)

    def test_material_unit_change_cannot_reinterpret_recipe_quantity(self):
        self.login()
        m=Material(name='TEST unidad vinculada',unit='hoja',unit_cost=Decimal('1'));db.session.add(m);db.session.commit()
        recipe=self.good_recipe();recipe.materials[0].material_id=m.id;db.session.commit()
        response=self.post('/admin/costos/materiales',dict(id=m.id,name=m.name,unit='metro',unit_cost='1',is_active='1'))
        self.assertEqual(response.status_code,400)
        db.session.refresh(m);self.assertEqual(m.unit,'hoja')
        self.assertEqual(recipe.materials[0].quantity,Decimal('0.5'))

    def test_material_and_recipe_pagination(self):
        self.login()
        for i in range(26): db.session.add(Material(name=f'TEST {i:02}',unit='hoja',unit_cost=Decimal(i)))
        db.session.commit()
        first=self.client.get('/admin/costos/materiales').get_data(as_text=True)
        second=self.client.get('/admin/costos/materiales?page=2').get_data(as_text=True)
        self.assertIn('TEST 24',first);self.assertNotIn('TEST 25',first);self.assertIn('TEST 25',second)
        recipe=self.good_recipe()
        for i in range(25):
            self.assertEqual(self.post(f'/admin/costos/recetas/{recipe.id}/duplicar',dict(product_id=self.pid,name=f'TEST copia {i}')).status_code,302)
        self.assertIn('Página 2',self.client.get('/admin/costos/recetas?page=2').get_data(as_text=True))
