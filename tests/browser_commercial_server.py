"""Disposable browser fixture. Never seeds users, prices or clients in tienda.db."""
import json
import os
import secrets
import sqlite3
import sys
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import create_app
from app.extensions import db
from app.models import Product, Category
from app.models.commercial import User,BusinessSettings,TaxSetting
from app.services.commercial import initialize_settings


def seed_portal_product():
    """Guarantee one public, customizable product for the customer-portal E2E."""
    category = Category.query.filter_by(slug='portal-e2e').first()
    if not category:
        category = Category(name='Fomix E2E', slug='portal-e2e')
        db.session.add(category)
        db.session.flush()
    if not Product.query.filter_by(code='FY.EZE.777').first():
        db.session.add(Product(code='FY.EZE.777', name='Figura E2E del portal',
                               slug='figura-e2e-del-portal', category_id=category.id,
                               description='Producto de prueba del portal de clientes.',
                               allows_customization=True, is_active=True, is_featured=False))


def main():
    folder=ROOT/'instance/commercial-check';folder.mkdir(exist_ok=True)
    database=folder/'browser.db'
    # Each run gets a new copy, preserving past test runs too.
    if database.exists():
        database=folder/('browser-'+secrets.token_hex(6)+'.db')
    with sqlite3.connect('file:'+str(ROOT/'instance/tienda.db')+'?mode=ro',uri=True) as source,sqlite3.connect(database) as target:
        source.backup(target)
    port=int(os.environ.get('BROWSER_PORT','5001'))
    email_e2e=os.environ.get('BROWSER_EMAIL_E2E') == '1' or '--email-e2e' in sys.argv
    app=create_app({'TESTING':True,'ENVIRONMENT':'testing','SECRET_KEY':secrets.token_hex(32),
                    'SESSION_COOKIE_SECURE':False,'BEHIND_PROXY':False,
                    'SQLALCHEMY_DATABASE_URI':'sqlite:///'+str(database),
                    'MAIL_ENABLED':email_e2e,'MAIL_BACKEND':'fake',
                    'MAIL_FROM_ADDRESS':'yoli@example.test','PUBLIC_BASE_URL':f'http://127.0.0.1:{port}',
                    'EMAIL_VERIFICATION_ENABLED':email_e2e,'ACCOUNT_RECOVERY_ENABLED':email_e2e,
                    'ORDER_EMAIL_NOTIFICATIONS_ENABLED':email_e2e})
    credentials={'admin':secrets.token_urlsafe(24),'vendedor':secrets.token_urlsafe(24)}
    if email_e2e:
        # Test fixture only: secret protected capture, never registered by create_app.
        from flask import request, abort, jsonify
        credentials['mail_capture'] = secrets.token_urlsafe(32)
        @app.get('/__test/mail')
        def capture_mail():
            if request.remote_addr != '127.0.0.1' or not secrets.compare_digest(
                    request.headers.get('X-Test-Key', ''), credentials['mail_capture']):
                abort(404)
            response = jsonify([{'to': str(m['To']), 'subject': str(m['Subject']), 'body': m.get_content()}
                                for m in app.extensions['mail_outbox']])
            response.headers['Cache-Control'] = 'no-store'
            return response
    with app.app_context():
        db.create_all();initialize_settings()
        if os.environ.get('BROWSER_PUBLIC_ONLY') != '1':
            seed_portal_product()
        for role in ('admin', 'vendedor'):
            password=credentials[role]
            u=User(username='browser_'+role,role=role);u.set_password(password);db.session.add(u)
        business=db.session.get(BusinessSettings,1);business.currency='USD'
        tax=db.session.get(TaxSetting,1);tax.percentage=Decimal('10');tax.name='Impuesto de prueba'
        db.session.commit()
    path=folder/'credentials.json'
    with open(path,'w',opener=lambda p,f:os.open(p,f,0o600)) as output: json.dump(credentials,output)
    port=int(os.environ.get('BROWSER_PORT','5001'))
    print(f'Servidor de pruebas aislado: http://127.0.0.1:{port}',flush=True)
    app.run(host='127.0.0.1',port=port,use_reloader=False)


if __name__=='__main__': main()
