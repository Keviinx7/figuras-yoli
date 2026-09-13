from datetime import datetime, timedelta, timezone
import hashlib
import re
import secrets
from flask import render_template,request,session,redirect,url_for,abort,current_app
from flask_login import login_user,logout_user,current_user,login_required
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import text
from app.extensions import db
from app.models.commercial import User,LoginAttempt
from app.services.costing import text_value
from . import bp

# Dummy hash keeps invalid-user password checks comparable; never an account password.
DUMMY_HASH=generate_password_hash(secrets.token_urlsafe(32),method='scrypt')


def validate_user(username,email):
    username=text_value(username,'Usuario',80,True).lower()
    email=text_value(email,'Correo',180).lower()
    if not re.fullmatch(r'[a-z0-9_.-]{3,80}',username): raise ValueError('Usuario: 3–80 letras, números, punto, guion o guion bajo.')
    if email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email): raise ValueError('Correo inválido.')
    return username,email


@bp.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('admin.dashboard'))
    error=None
    if request.method=='POST':
        db.session.execute(text('BEGIN IMMEDIATE'))
        username=request.form.get('username','').strip().lower()[:80]
        password=request.form.get('password','')
        now=datetime.now(timezone.utc).replace(tzinfo=None)
        key=hashlib.sha256((request.remote_addr or 'local').encode()).hexdigest()
        attempt=db.session.get(LoginAttempt,key)
        if attempt and now-attempt.window_start<timedelta(minutes=15) and attempt.failures>=10:
            db.session.rollback()
            return render_template('auth/login.html',error='Demasiados intentos. Espere 15 minutos.'),429
        user=User.query.filter_by(username=username).first()
        valid=check_password_hash(user.password_hash if user else DUMMY_HASH,password[:200])
        if user and user.is_active and valid and len(password)<=200:
            if attempt: db.session.delete(attempt)
            user.last_login=now;db.session.commit()
            session.clear();login_user(user,remember=False,fresh=True)
            session.permanent=True;session['csrf_token']=secrets.token_hex(24)
            return redirect(url_for('admin.dashboard'))  # Never trust an external next URL.
        if not attempt:
            attempt=LoginAttempt(key=key,failures=0,window_start=now);db.session.add(attempt)
        if now-attempt.window_start>=timedelta(minutes=15): attempt.window_start=now;attempt.failures=0
        attempt.failures+=1;db.session.commit()
        error='Usuario o contraseña incorrectos.'
    return render_template('auth/login.html',error=error),401 if error else 200


@bp.post('/logout')
@login_required
def logout():
    logout_user();session.clear()
    return redirect(url_for('auth.login'))
