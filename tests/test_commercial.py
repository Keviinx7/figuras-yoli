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
                                  CostEstimate,AuditEvent,BusinessSettings,TaxSetting)
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
        for path in ['/admin','/admin/clientes','/admin/costos','/admin/cotizaciones','/admin/facturas','/admin/configuracion','/admin/usuarios']:
            self.assertEqual(self.client.get(path).status_code,302)
        self.login()
        for method in ['post','put','patch','delete']:
            self.assertEqual(getattr(self.client,method)('/admin/clientes/nuevo').status_code,400)
        self.assertEqual(self.client.post('/logout').status_code,400)

    def test_seller_roles(self):
        self.login('seller')
        for path in ['/admin','/admin/productos','/admin/clientes','/admin/costos','/admin/cotizaciones','/admin/facturas']:
            self.assertEqual(self.client.get(path).status_code,200,path)
        for path in ['/admin/usuarios','/admin/configuracion','/admin/categorias','/admin/costos/materiales',f'/admin/productos/{self.pid}/editar']:
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

    def test_calculator_persists_exact_values(self):
        self.login('seller');self.configure()
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
        self.login('seller');self.configure();self.post('/admin/costos',self.cost_payload());e=CostEstimate.query.one()
        payload=self.quote_payload(e.id);payload['total']='0.01'
        self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,302)
        self.assertEqual(Quote.query.one().total,Decimal('6.336'))
        payload['item_unit_price']=['0.01'];self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,403)
        payload['item_unit_price']=[''];payload['item_discount']=['1'];self.assertEqual(self.post('/admin/cotizaciones/nueva',payload).status_code,403)

    def test_seller_manual_quote_denied(self):
        self.login('seller');self.configure();self.assertEqual(self.post('/admin/cotizaciones/nueva',self.quote_payload()).status_code,400)

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
